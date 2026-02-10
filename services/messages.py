"""
Lead Messages service.
Send messages to leads via email/SMS/WhatsApp.
"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import LeadMessage


async def create_message(
    db: AsyncSession,
    subject: str,
    body: str,
    send_method: str | None = None,
    recipient_type: str | None = None,
    lead_id: int | None = None,
    campaign_id: int | None = None,
    salesperson_id: int | None = None,
    phone: str | None = None,
) -> LeadMessage:
    """Create a message draft."""
    message = LeadMessage(
        subject=subject,
        body=body,
        send_method=send_method,
        recipient_type=recipient_type,
        lead_id=lead_id,
        campaign_id=campaign_id,
        salesperson_id=salesperson_id,
        phone=phone,
        status="טיוטה",
    )
    db.add(message)
    await db.flush()
    return message


async def mark_sent(db: AsyncSession, message_id: int) -> LeadMessage | None:
    """Mark a message as sent."""
    stmt = select(LeadMessage).where(LeadMessage.id == message_id)
    result = await db.execute(stmt)
    msg = result.scalar_one_or_none()
    if not msg:
        return None
    msg.status = "נשלח"
    msg.sent_at = func.now()
    await db.flush()
    return msg


async def mark_failed(db: AsyncSession, message_id: int) -> LeadMessage | None:
    """Mark a message as failed."""
    stmt = select(LeadMessage).where(LeadMessage.id == message_id)
    result = await db.execute(stmt)
    msg = result.scalar_one_or_none()
    if not msg:
        return None
    msg.status = "נכשל"
    await db.flush()
    return msg


async def list_messages(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[LeadMessage]:
    """List messages with optional status filter."""
    stmt = select(LeadMessage).order_by(LeadMessage.created_at.desc()).limit(limit).offset(offset)
    if status:
        stmt = stmt.where(LeadMessage.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())
