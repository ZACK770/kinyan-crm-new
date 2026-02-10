"""
Communications service.
Logging calls, scheduling follow-ups.
"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import LeadInteraction, Lead


async def log_call(
    db: AsyncSession,
    lead_id: int,
    user_name: str | None = None,
    description: str | None = None,
    next_call_date: datetime | None = None,
) -> LeadInteraction:
    """Log an outbound call to a lead."""
    interaction = LeadInteraction(
        lead_id=lead_id,
        interaction_type="outbound_call",
        user_name=user_name,
        description=description,
        next_call_date=next_call_date,
    )
    db.add(interaction)

    # Update lead's last contact date
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if lead and lead.status == "ליד חדש":
        lead.status = "חיוג ראשון"

    await db.flush()
    return interaction


async def get_pending_followups(db: AsyncSession, salesperson_id: int | None = None) -> list[LeadInteraction]:
    """Get interactions with pending follow-up dates."""
    stmt = (
        select(LeadInteraction)
        .where(
            LeadInteraction.next_call_date.isnot(None),
            LeadInteraction.next_call_date >= datetime.now(),
        )
        .order_by(LeadInteraction.next_call_date.asc())
        .limit(50)
    )

    if salesperson_id:
        stmt = stmt.join(Lead).where(Lead.salesperson_id == salesperson_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())
