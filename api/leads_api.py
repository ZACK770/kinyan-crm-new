"""
Leads API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import leads as lead_svc

router = APIRouter(prefix="/leads", tags=["leads"])


# ── Schemas ──────────────────────────────────────────
class LeadCreate(BaseModel):
    name: str = ""
    phone: str
    email: str | None = None
    city: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    campaign_name: str | None = None
    source_message: str | None = None


class LeadUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    status: str | None = None
    notes: str | None = None
    salesperson_id: int | None = None


class InteractionCreate(BaseModel):
    interaction_type: str = "generic"
    description: str | None = None
    user_name: str | None = None
    next_call_date: datetime | None = None


# ── Endpoints ────────────────────────────────────────
@router.get("/")
async def list_leads(
    status: str | None = Query(None),
    salesperson_id: int | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    items = await lead_svc.list_leads(db, status=status, salesperson_id=salesperson_id, limit=limit, offset=offset)
    return [
        {
            "id": l.id,
            "full_name": l.full_name,
            "phone": l.phone,
            "status": l.status,
            "salesperson_id": l.salesperson_id,
            "created_at": str(l.created_at),
        }
        for l in items
    ]


@router.get("/search")
async def search_lead(phone: str = Query(...), db: AsyncSession = Depends(get_db)):
    lead = await lead_svc.search_by_phone(db, phone)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {"id": lead.id, "full_name": lead.full_name, "phone": lead.phone, "status": lead.status}


@router.get("/{lead_id}")
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await lead_svc.get_lead_with_history(db, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {
        "id": lead.id,
        "full_name": lead.full_name,
        "phone": lead.phone,
        "email": lead.email,
        "status": lead.status,
        "salesperson_id": lead.salesperson_id,
        "created_at": str(lead.created_at),
        "interactions": [
            {
                "id": i.id,
                "type": i.interaction_type,
                "description": i.description,
                "created_at": str(i.created_at),
            }
            for i in (lead.interactions or [])
        ],
    }


@router.post("/")
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db)):
    result = await lead_svc.process_incoming_lead(db, **data.model_dump())
    return result


@router.patch("/{lead_id}")
async def update_lead(lead_id: int, data: LeadUpdate, db: AsyncSession = Depends(get_db)):
    lead = await lead_svc.update_lead(db, lead_id, **data.model_dump(exclude_unset=True))
    if not lead:
        raise HTTPException(404, "Lead not found")
    await db.commit()
    return {"id": lead.id, "status": lead.status}


@router.post("/{lead_id}/interactions")
async def add_interaction(lead_id: int, data: InteractionCreate, db: AsyncSession = Depends(get_db)):
    interaction = await lead_svc.add_interaction(db, lead_id, **data.model_dump())
    await db.commit()
    return {"id": interaction.id}
