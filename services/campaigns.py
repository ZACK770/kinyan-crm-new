"""
Campaigns service - CRUD operations for campaigns
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Campaign, CampaignSalespersonLink, CampaignLandingLink


async def get_campaigns(db: AsyncSession, active_only: bool = False) -> list[Campaign]:
    """Get all campaigns, optionally filtering by active status."""
    stmt = select(Campaign).order_by(Campaign.created_at.desc())
    if active_only:
        stmt = stmt.where(Campaign.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_campaign(db: AsyncSession, campaign_id: int) -> Campaign | None:
    """Get single campaign by ID with related data."""
    stmt = (
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .options(
            selectinload(Campaign.salesperson_links),
            selectinload(Campaign.landing_links),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_campaign(db: AsyncSession, **kwargs) -> Campaign:
    """Create a new campaign."""
    campaign = Campaign(
        name=kwargs.get("name", ""),
        course_id=kwargs.get("course_id"),
        campaign_type=kwargs.get("campaign_type"),
        platforms=kwargs.get("platforms"),
        start_date=kwargs.get("start_date"),
        end_date=kwargs.get("end_date"),
        form_name=kwargs.get("form_name"),
        landing_page_url=kwargs.get("landing_page_url"),
        description=kwargs.get("description"),
        is_active=kwargs.get("is_active", True),
    )
    db.add(campaign)
    await db.flush()
    return campaign


async def update_campaign(db: AsyncSession, campaign_id: int, **kwargs) -> Campaign | None:
    """Update campaign fields."""
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(campaign, key):
            setattr(campaign, key, value)

    await db.flush()
    return campaign


async def delete_campaign(db: AsyncSession, campaign_id: int) -> bool:
    """Soft delete (deactivate) a campaign."""
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign:
        return False

    campaign.is_active = False
    await db.flush()
    return True

