"""
Campaigns API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import campaigns as campaign_svc
from services import audit_logs
from .dependencies import require_entity_access

router = APIRouter(tags=["campaigns"])


# ── Schemas ──────────────────────────────────────────
class CampaignCreate(BaseModel):
    name: str
    course_id: int | None = None
    platforms: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    landing_page_url: str | None = None
    description: str | None = None
    is_active: bool = True


class CampaignUpdate(BaseModel):
    name: str | None = None
    course_id: int | None = None
    platforms: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    landing_page_url: str | None = None
    description: str | None = None
    is_active: bool | None = None


# ── Endpoints ────────────────────────────────────────
@router.get("/")
async def list_campaigns(
    active_only: bool = Query(False),
    user = Depends(require_entity_access("campaigns", "view")),
    db: AsyncSession = Depends(get_db)
):
    items = await campaign_svc.get_campaigns(db, active_only=active_only)
    return [
        {
            "id": c.id,
            "name": c.name,
            "course_id": c.course_id,
            "platforms": c.platforms,
            "start_date": str(c.start_date) if c.start_date else None,
            "end_date": str(c.end_date) if c.end_date else None,
            "is_active": c.is_active,
            "created_at": str(c.created_at),
        }
        for c in items
    ]


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    user = Depends(require_entity_access("campaigns", "view")),
    db: AsyncSession = Depends(get_db)
):
    campaign = await campaign_svc.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return {
        "id": campaign.id,
        "name": campaign.name,
        "course_id": campaign.course_id,
        "platforms": campaign.platforms,
        "start_date": str(campaign.start_date) if campaign.start_date else None,
        "end_date": str(campaign.end_date) if campaign.end_date else None,
        "landing_page_url": campaign.landing_page_url,
        "description": campaign.description,
        "is_active": campaign.is_active,
        "created_at": str(campaign.created_at),
        "salesperson_links": [
            {"id": l.id, "salesperson_id": l.salesperson_id, "message_text": l.message_text}
            for l in campaign.salesperson_links
        ],
        "landing_links": [
            {"id": l.id, "source_label": l.source_label, "url_with_source": l.url_with_source}
            for l in campaign.landing_links
        ],
    }


@router.post("/")
async def create_campaign(
    data: CampaignCreate,
    request: Request,
    user = Depends(require_entity_access("campaigns", "create")),
    db: AsyncSession = Depends(get_db)
):
    campaign = await campaign_svc.create_campaign(db, **data.model_dump())
    await db.commit()
    
    await audit_logs.log_create(
        db=db,
        user=user,
        entity_type="campaigns",
        entity_id=campaign.id,
        description=f"נוצר קמפיין: {data.name}",
        request=request,
    )
    
    return {"id": campaign.id, "name": campaign.name}


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    request: Request,
    user = Depends(require_entity_access("campaigns", "edit")),
    db: AsyncSession = Depends(get_db)
):
    campaign = await campaign_svc.update_campaign(db, campaign_id, **data.model_dump(exclude_unset=True))
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    await db.commit()
    
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="campaigns",
        entity_id=campaign_id,
        description=f"עודכן קמפיין: {campaign.name}",
        changes=data.model_dump(exclude_unset=True),
        request=request,
    )
    
    return {"id": campaign.id, "name": campaign.name}


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    request: Request,
    user = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db)
):
    success = await campaign_svc.delete_campaign(db, campaign_id)
    if not success:
        raise HTTPException(404, "Campaign not found")
    await db.commit()
    
    await audit_logs.log_delete(
        db=db,
        user=user,
        entity_type="campaigns",
        entity_id=campaign_id,
        description="קמפיין בוטל",
        request=request,
    )
    
    return {"success": True}
