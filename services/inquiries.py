"""
Inquiries service.
Handle incoming inquiries (email, voicemail, phone, etc.)
"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Inquiry, InquiryResponse


async def create_inquiry(
    db: AsyncSession,
    subject: str,
    inquiry_type: str,
    lead_id: int | None = None,
    student_id: int | None = None,
    phone: str | None = None,
    notes: str | None = None,
) -> Inquiry:
    """Create a new inquiry."""
    inquiry = Inquiry(
        subject=subject,
        inquiry_type=inquiry_type,
        lead_id=lead_id,
        student_id=student_id,
        phone=phone,
        notes=notes,
    )
    db.add(inquiry)
    await db.flush()
    return inquiry


async def add_response(
    db: AsyncSession,
    inquiry_id: int,
    author: str | None = None,
    content: str | None = None,
) -> InquiryResponse:
    """Add a response to an inquiry thread."""
    response = InquiryResponse(
        inquiry_id=inquiry_id,
        author=author,
        content=content,
    )
    db.add(response)
    await db.flush()
    return response


async def update_inquiry_status(
    db: AsyncSession,
    inquiry_id: int,
    status: str,
    handled_by: str | None = None,
) -> Inquiry | None:
    """Update inquiry status."""
    stmt = select(Inquiry).where(Inquiry.id == inquiry_id)
    result = await db.execute(stmt)
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        return None

    inquiry.status = status
    if handled_by:
        inquiry.handled_by = handled_by
    await db.flush()
    return inquiry


async def get_inquiry_with_responses(db: AsyncSession, inquiry_id: int) -> Inquiry | None:
    """Get an inquiry with all its responses."""
    stmt = (
        select(Inquiry)
        .where(Inquiry.id == inquiry_id)
        .options(selectinload(Inquiry.responses))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_inquiries(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Inquiry]:
    """List inquiries with optional status filter."""
    stmt = select(Inquiry).order_by(Inquiry.created_at.desc()).limit(limit).offset(offset)
    if status:
        stmt = stmt.where(Inquiry.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())
