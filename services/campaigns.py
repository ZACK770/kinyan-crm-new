"""
Campaigns service.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Campaign


async def get_campaigns(db: AsyncSession, active_only: bool = True) -> list[Campaign]:
    """Get all campaigns."""
    stmt = select(Campaign).order_by(Campaign.created_at.desc())
    if active_only:
        stmt = stmt.where(Campaign.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_campaign(db: AsyncSession, name: str, campaign_type: str | None = None) -> Campaign:
    """Create a new campaign."""
    campaign = Campaign(name=name, campaign_type=campaign_type)
    db.add(campaign)
    await db.flush()
    return campaign
