"""
Inbound Emails API — view, filter, assign emails to leads.
Prefix: /api/inbound-emails
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from db import get_db
from db.models import InboundEmail, File
from services import inbound_emails as svc
from .dependencies import require_entity_access, require_permission
from sqlalchemy import select

router = APIRouter(tags=["inbound-emails"])


# ── Schemas ──────────────────────────────────────────
class EmailListItem(BaseModel):
    id: int
    gmail_id: str
    thread_id: str | None
    direction: str
    from_email: str
    from_name: str | None
    to_emails: list[dict] | None = None
    subject: str | None
    snippet: str | None
    has_attachment: bool
    attachments_count: int
    folder: str | None
    lead_id: int | None
    lead_name: str | None = None
    matched_auto: bool
    is_read: bool
    email_date: str | None
    created_at: str


class EmailDetail(EmailListItem):
    body_text: str | None
    body_html: str | None
    bcc_emails: list[dict] | None = None
    label_ids: list[str] | None = None
    message_id_header: str | None
    in_reply_to: str | None
    size_estimate: int | None
    history_id: str | None
    attachments: list[dict] = []
    thread_emails: list[dict] = []


class AssignLeadRequest(BaseModel):
    lead_id: int | None = None


class EmailListResponse(BaseModel):
    items: list[EmailListItem]
    total: int


# ── Helpers ──────────────────────────────────────────
def _safe_json_parse(val: str | None) -> list | None:
    if not val:
        return None
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


def _email_to_list_item(email: InboundEmail) -> dict:
    lead_name = None
    if email.lead and hasattr(email.lead, 'full_name'):
        lead_name = email.lead.full_name
        if hasattr(email.lead, 'family_name') and email.lead.family_name:
            lead_name += f" {email.lead.family_name}"

    return {
        "id": email.id,
        "gmail_id": email.gmail_id,
        "thread_id": email.thread_id,
        "direction": email.direction,
        "from_email": email.from_email,
        "from_name": email.from_name,
        "to_emails": _safe_json_parse(email.to_emails),
        "subject": email.subject,
        "snippet": email.snippet,
        "has_attachment": email.has_attachment,
        "attachments_count": email.attachments_count,
        "folder": email.folder,
        "lead_id": email.lead_id,
        "lead_name": lead_name,
        "matched_auto": email.matched_auto,
        "is_read": email.is_read,
        "email_date": email.email_date.isoformat() if email.email_date else None,
        "created_at": email.created_at.isoformat() if email.created_at else "",
    }


# ── Endpoints ──────────────────────────────────────────

@router.get("/", response_model=EmailListResponse)
async def list_inbound_emails(
    direction: str | None = Query(None, description="inbound / outbound"),
    folder: str | None = Query(None, description="INBOX / SENT"),
    lead_id: int | None = Query(None),
    is_read: bool | None = Query(None),
    unmatched: bool = Query(False, description="Only unmatched emails"),
    search: str | None = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    user=Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List inbound/outbound emails with filters."""
    items, total = await svc.list_emails(
        db=db,
        direction=direction,
        folder=folder,
        lead_id=lead_id,
        is_read=is_read,
        unmatched_only=unmatched,
        search=search,
        limit=limit,
        offset=offset,
    )

    # Eager load lead names
    from sqlalchemy.orm import selectinload
    for item in items:
        if item.lead_id and not item.lead:
            # Already loaded via relationship
            pass

    return {
        "items": [_email_to_list_item(e) for e in items],
        "total": total,
    }


@router.get("/unread-count")
async def get_unread_count(
    user=Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread inbound emails."""
    count = await svc.get_unread_count(db)
    return {"count": count}


@router.get("/{email_id}")
async def get_email_detail(
    email_id: int,
    user=Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get full email detail including body, thread, and attachments."""
    email = await svc.get_email(db, email_id)
    if not email:
        raise HTTPException(404, "Email not found")

    # Mark as read
    if not email.is_read:
        email.is_read = True
        await db.flush()
        await db.commit()

    # Get attachments from files table
    attachments = []
    if email.has_attachment:
        att_result = await db.execute(
            select(File).where(
                File.entity_type == "inbound_email",
                File.entity_id == email.id,
            )
        )
        for f in att_result.scalars().all():
            attachments.append({
                "id": f.id,
                "filename": f.filename,
                "size_bytes": f.size_bytes,
                "content_type": f.content_type,
            })

    # Get thread emails
    thread_emails = []
    if email.thread_id:
        thread = await svc.get_thread(db, email.thread_id)
        thread_emails = [
            {
                "id": e.id,
                "direction": e.direction,
                "from_name": e.from_name,
                "from_email": e.from_email,
                "subject": e.subject,
                "snippet": e.snippet,
                "email_date": e.email_date.isoformat() if e.email_date else None,
                "has_attachment": e.has_attachment,
                "is_current": e.id == email.id,
            }
            for e in thread
        ]

    base = _email_to_list_item(email)
    base.update({
        "body_text": email.body_text,
        "body_html": email.body_html,
        "bcc_emails": _safe_json_parse(email.bcc_emails),
        "label_ids": _safe_json_parse(email.label_ids),
        "message_id_header": email.message_id_header,
        "in_reply_to": email.in_reply_to,
        "size_estimate": email.size_estimate,
        "history_id": email.history_id,
        "attachments": attachments,
        "thread_emails": thread_emails,
    })

    return base


@router.patch("/{email_id}/assign")
async def assign_email_to_lead(
    email_id: int,
    data: AssignLeadRequest,
    user=Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Assign or unassign a lead to an email."""
    email = await svc.assign_lead(db, email_id, data.lead_id)
    if not email:
        raise HTTPException(404, "Email not found")
    await db.commit()
    return {"status": "ok", "lead_id": email.lead_id}


@router.patch("/{email_id}/read")
async def mark_email_read(
    email_id: int,
    read: bool = Query(True),
    user=Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Mark email as read/unread."""
    email = await svc.mark_read(db, email_id, read)
    if not email:
        raise HTTPException(404, "Email not found")
    await db.commit()
    return {"status": "ok", "is_read": email.is_read}


@router.get("/lead/{lead_id}/emails")
async def get_lead_emails(
    lead_id: int,
    limit: int = Query(100, le=500),
    user=Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get all inbound/outbound emails associated with a lead."""
    items, total = await svc.list_emails(db=db, lead_id=lead_id, limit=limit)
    return {
        "items": [_email_to_list_item(e) for e in items],
        "total": total,
    }
