"""
Leads API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import leads as lead_svc
from services import audit_logs
from .dependencies import require_entity_access
from .schemas import LeadCreate, LeadUpdate, SalespersonResponse

router = APIRouter(tags=["leads"])


# ── Local Schemas (not in shared schemas.py) ──────────
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
    user = Depends(require_entity_access("leads", "view")),
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
async def search_lead(
    phone: str = Query(...),
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db)
):
    lead = await lead_svc.search_by_phone(db, phone)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {"id": lead.id, "full_name": lead.full_name, "phone": lead.phone, "status": lead.status}


@router.get("/salespersons")
async def get_salespersons(
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get list of active salespeople for lead assignment."""
    from services import sales as sales_svc
    salespeople = await sales_svc.get_active_salespeople(db)
    return [
        {"id": sp.id, "name": sp.name, "email": sp.email, "phone": sp.phone}
        for sp in salespeople
    ]


@router.get("/{lead_id}")
async def get_lead(
    lead_id: int,
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db)
):
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
async def create_lead(
    data: LeadCreate,
    request: Request,
    user = Depends(require_entity_access("leads", "create")),
    db: AsyncSession = Depends(get_db)
):
    result = await lead_svc.process_incoming_lead(db, **data.model_dump())
    
    # Log lead creation
    if result and "lead_id" in result:
        await audit_logs.log_create(
            db=db,
            user=user,
            entity_type="leads",
            entity_id=result["lead_id"],
            description=f"נוצר ליד חדש: {data.full_name} - {data.phone}",
            request=request,
        )
    
    return result


@router.patch("/{lead_id}")
async def update_lead(
    lead_id: int,
    data: LeadUpdate,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    lead = await lead_svc.update_lead(db, lead_id, **data.model_dump(exclude_unset=True))
    if not lead:
        raise HTTPException(404, "Lead not found")
    await db.commit()
    
    # Log lead update
    changes = data.model_dump(exclude_unset=True)
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="leads",
        entity_id=lead_id,
        description=f"עודכן ליד: {lead.full_name}",
        changes=changes,
        request=request,
    )
    
    return {"id": lead.id, "status": lead.status}


# ── Convert Lead to Student ────────────────────────────────
class ConvertLeadRequest(BaseModel):
    course_id: int | None = None


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: int,
    data: ConvertLeadRequest,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """Convert a lead to a student, optionally enrolling in a course."""
    result = await lead_svc.convert_lead_to_student(db, lead_id, course_id=data.course_id)
    
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Conversion failed"))
    
    # Log conversion
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="leads",
        entity_id=lead_id,
        description=f"ליד הומר לתלמיד #{result.get('student_id')}",
        changes={"action": "converted", "student_id": result.get("student_id"), "course_id": data.course_id},
        request=request,
    )
    
    return result


@router.post("/{lead_id}/interactions")
async def add_interaction(
    lead_id: int,
    data: InteractionCreate,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    interaction = await lead_svc.add_interaction(db, lead_id, **data.model_dump())
    await db.commit()
    return {"id": interaction.id}
