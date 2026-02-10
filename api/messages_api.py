"""
Messages API — send emails to leads, track sent messages.
Prefix: /api/messages
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import get_db
from db.models import Lead, LeadMessage, Inquiry, LeadInteraction
from services import messages as msg_svc
from services.email_service import send_lead_email
from .dependencies import require_entity_access

router = APIRouter(tags=["messages"])


# ── Schemas ──────────────────────────────────────────
class SendEmailRequest(BaseModel):
    lead_id: int
    subject: str
    body: str  # HTML body content


class SendEmailResponse(BaseModel):
    message_id: int
    status: str
    detail: str


# ── Send email to a lead ─────────────────────────────
@router.post("/send-email", response_model=SendEmailResponse)
async def send_email_to_lead(
    data: SendEmailRequest,
    user=Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """
    Send an email to a lead.
    - Saves the message in lead_messages table
    - Actually sends via SMTP
    - Adds an interaction record to the lead's history
    - On failure, marks the message as failed
    """
    # Get lead with email
    stmt = select(Lead).where(Lead.id == data.lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "ליד לא נמצא")
    if not lead.email:
        raise HTTPException(400, "לליד אין כתובת מייל")

    # Create message record (draft)
    message = await msg_svc.create_message(
        db=db,
        subject=data.subject,
        body=data.body,
        send_method="מייל",
        recipient_type="lead",
        lead_id=data.lead_id,
    )
    await db.flush()

    # Send via SMTP
    success = await send_lead_email(
        to_email=lead.email,
        subject=data.subject,
        body_html=data.body,
    )

    if success:
        await msg_svc.mark_sent(db, message.id)

        # Add interaction to lead history
        interaction = LeadInteraction(
            lead_id=data.lead_id,
            interaction_type="email",
            description=f"נשלח מייל: {data.subject}",
            user_name=user.full_name if hasattr(user, 'full_name') else None,
        )
        db.add(interaction)

        await db.commit()
        return SendEmailResponse(
            message_id=message.id,
            status="נשלח",
            detail=f"המייל נשלח בהצלחה ל-{lead.email}",
        )
    else:
        await msg_svc.mark_failed(db, message.id)
        await db.commit()
        raise HTTPException(500, "שליחת המייל נכשלה. בדוק את הגדרות ה-SMTP")


# ── List all sent messages ────────────────────────────
@router.get("/")
async def list_messages(
    status: str | None = Query(None),
    lead_id: int | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user=Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List messages with optional filters."""
    stmt = (
        select(LeadMessage)
        .order_by(LeadMessage.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(LeadMessage.status == status)
    if lead_id:
        stmt = stmt.where(LeadMessage.lead_id == lead_id)

    result = await db.execute(stmt)
    items = result.scalars().all()

    return [
        {
            "id": m.id,
            "subject": m.subject,
            "body": m.body,
            "status": m.status,
            "send_method": m.send_method,
            "lead_id": m.lead_id,
            "created_at": str(m.created_at),
            "sent_at": str(m.sent_at) if m.sent_at else None,
        }
        for m in items
    ]


# ── Get messages for a specific lead ──────────────────
@router.get("/lead/{lead_id}")
async def get_lead_messages(
    lead_id: int,
    user=Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages sent to a specific lead."""
    stmt = (
        select(LeadMessage)
        .where(LeadMessage.lead_id == lead_id)
        .order_by(LeadMessage.created_at.desc())
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    return [
        {
            "id": m.id,
            "subject": m.subject,
            "body": m.body,
            "status": m.status,
            "send_method": m.send_method,
            "created_at": str(m.created_at),
            "sent_at": str(m.sent_at) if m.sent_at else None,
        }
        for m in items
    ]
