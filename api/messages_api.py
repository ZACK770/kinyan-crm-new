"""
Messages API — send emails to leads, track sent messages.
Prefix: /api/messages
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from db import get_db
from db.models import Lead, LeadMessage, Inquiry, LeadInteraction, EmailTemplate, File
from services import messages as msg_svc
from services.email_service import send_lead_email
from services.storage import storage_service
from .dependencies import require_entity_access

router = APIRouter(tags=["messages"])


# ── Schemas ──────────────────────────────────────────
class SendEmailRequest(BaseModel):
    lead_id: int
    subject: str
    body: str  # HTML body content
    template_id: Optional[int] = None
    file_ids: List[int] = []  # IDs of already-uploaded files to attach


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
    Send an email to a lead with optional attachments.
    - Saves the message in lead_messages table
    - Actually sends via SMTP with attachments
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
    
    # Update template_id if provided
    if data.template_id:
        message.template_id = data.template_id
    
    await db.flush()

    # Prepare attachments if file_ids provided
    attachments = []
    if data.file_ids:
        for file_id in data.file_ids:
            file_result = await db.execute(select(File).where(File.id == file_id))
            file_obj = file_result.scalar_one_or_none()
            if file_obj:
                try:
                    content = None
                    # Check if file is stored in DB
                    if file_obj.file_data:
                        content = file_obj.file_data
                    # Otherwise try R2
                    elif file_obj.storage_key:
                        presigned_url = await storage_service.get_presigned_url(file_obj.storage_key)
                        if presigned_url:
                            import aiohttp
                            async with aiohttp.ClientSession() as session:
                                async with session.get(presigned_url) as resp:
                                    if resp.status == 200:
                                        content = await resp.read()
                    
                    if content:
                        attachments.append({
                            'filename': file_obj.filename,
                            'content': content,
                            'content_type': file_obj.content_type or 'application/octet-stream'
                        })
                except Exception as e:
                    # Log but don't fail - continue without this attachment
                    print(f"ATTACH ERROR for file {file_id}: {e}")
                    import traceback; traceback.print_exc()
        
        # Link files to message
        for file_id in data.file_ids:
            file_result = await db.execute(select(File).where(File.id == file_id))
            file_obj = file_result.scalar_one_or_none()
            if file_obj and file_obj.entity_type == "temp":
                # Move temp file to message
                file_obj.entity_type = "messages"
                file_obj.entity_id = message.id

    # Send via SMTP
    success = await send_lead_email(
        to_email=lead.email,
        subject=data.subject,
        body_html=data.body,
        attachments=attachments if attachments else None,
    )

    if success:
        await msg_svc.mark_sent(db, message.id)

        # Add interaction to lead history
        interaction = LeadInteraction(
            lead_id=data.lead_id,
            interaction_type="email",
            description=f"נשלח מייל: {data.subject}" + (f" ({len(attachments)} קבצים מצורפים)" if attachments else ""),
            user_name=user.full_name if hasattr(user, 'full_name') else None,
        )
        db.add(interaction)

        await db.commit()
        return SendEmailResponse(
            message_id=message.id,
            status="נשלח",
            detail=f"המייל נשלח בהצלחה ל-{lead.email}" + (f" עם {len(attachments)} קבצים מצורפים" if attachments else ""),
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
    """Get all messages sent to a specific lead with attachments."""
    stmt = (
        select(LeadMessage)
        .where(LeadMessage.lead_id == lead_id)
        .order_by(LeadMessage.created_at.desc())
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    response = []
    for m in items:
        # Get attachments for this message
        attachments_query = select(File).where(
            File.entity_type == "messages",
            File.entity_id == m.id
        )
        attachments_result = await db.execute(attachments_query)
        attachments = attachments_result.scalars().all()
        
        response.append({
            "id": m.id,
            "subject": m.subject,
            "body": m.body,
            "status": m.status,
            "send_method": m.send_method,
            "created_at": str(m.created_at),
            "sent_at": str(m.sent_at) if m.sent_at else None,
            "attachments": [
                {
                    "id": a.id,
                    "filename": a.filename,
                    "size_bytes": a.size_bytes,
                    "content_type": a.content_type,
                }
                for a in attachments
            ]
        })
    
    return response
