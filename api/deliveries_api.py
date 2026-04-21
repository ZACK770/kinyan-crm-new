"""
Deliveries API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from db import get_db
from services import deliveries as delivery_svc
from .dependencies import require_entity_access

router = APIRouter(tags=["deliveries"])


# ── Schemas ────────────────────────────────────────────
class DeliveryCreate(BaseModel):
    lead_id: int


class DeliveryUpdate(BaseModel):
    full_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: int
    lead_id: int
    full_name: str
    address: Optional[str]
    city: Optional[str]
    phone: str
    email: Optional[str]
    is_sent: bool
    sent_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# ── Endpoints ──────────────────────────────────────────
@router.get("/pending")
async def get_pending_deliveries(
    db: AsyncSession = Depends(get_db),
):
    """
    מחזיר רשימה של משלומים שעדיין לא נשלחו
    """
    deliveries = await delivery_svc.get_pending_deliveries(db)
    return [
        {
            "id": d.id,
            "lead_id": d.lead_id,
            "full_name": d.full_name,
            "address": d.address,
            "city": d.city,
            "phone": d.phone,
            "email": d.email,
            "is_sent": d.is_sent,
            "sent_date": str(d.sent_date) if d.sent_date else None,
            "notes": d.notes,
            "created_at": str(d.created_at),
            "updated_at": str(d.updated_at),
        }
        for d in deliveries
    ]


@router.get("/history")
async def get_delivery_history(
    db: AsyncSession = Depends(get_db),
):
    """
    מחזיר רשימה של משלומים שכבר נשלחו (היסטוריה)
    """
    deliveries = await delivery_svc.get_delivery_history(db)
    return [
        {
            "id": d.id,
            "lead_id": d.lead_id,
            "full_name": d.full_name,
            "address": d.address,
            "city": d.city,
            "phone": d.phone,
            "email": d.email,
            "is_sent": d.is_sent,
            "sent_date": str(d.sent_date) if d.sent_date else None,
            "notes": d.notes,
            "created_at": str(d.created_at),
            "updated_at": str(d.updated_at),
        }
        for d in deliveries
    ]


@router.post("/create-from-lead/{lead_id}")
async def create_delivery_from_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    יוצר רשומת משלוח חדשה מליד
    """
    from db.models import Lead
    from sqlalchemy import select
    
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(404, "Lead not found")
    
    delivery = await delivery_svc.create_delivery_from_lead(db, lead)
    await db.commit()
    
    return {
        "id": delivery.id,
        "lead_id": delivery.lead_id,
        "full_name": delivery.full_name,
        "address": delivery.address,
        "city": delivery.city,
        "phone": delivery.phone,
        "email": delivery.email,
        "is_sent": delivery.is_sent,
        "sent_date": str(delivery.sent_date) if delivery.sent_date else None,
        "notes": delivery.notes,
        "created_at": str(delivery.created_at),
        "updated_at": str(delivery.updated_at),
    }


@router.put("/{delivery_id}/mark-sent")
async def mark_delivery_sent(
    delivery_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    מסמן משלוץ כנשלח ומעדכן את תאריך השליחה
    """
    result = await delivery_svc.mark_delivery_sent(db, delivery_id, user_id=None)
    
    if not result["success"]:
        raise HTTPException(404, result["error"])
    
    await db.commit()
    
    delivery = result["delivery"]
    return {
        "id": delivery.id,
        "lead_id": delivery.lead_id,
        "full_name": delivery.full_name,
        "address": delivery.address,
        "city": delivery.city,
        "phone": delivery.phone,
        "email": delivery.email,
        "is_sent": delivery.is_sent,
        "sent_date": str(delivery.sent_date) if delivery.sent_date else None,
        "notes": delivery.notes,
        "created_at": str(delivery.created_at),
        "updated_at": str(delivery.updated_at),
    }


@router.put("/{delivery_id}")
async def update_delivery(
    delivery_id: int,
    update_data: DeliveryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    מעדכן פרטי משלוח
    """
    result = await delivery_svc.update_delivery(
        db,
        delivery_id,
        full_name=update_data.full_name,
        address=update_data.address,
        city=update_data.city,
        phone=update_data.phone,
        email=update_data.email,
        notes=update_data.notes,
        user_id=None
    )
    
    if not result["success"]:
        raise HTTPException(404, result["error"])
    
    await db.commit()
    
    delivery = result["delivery"]
    return {
        "id": delivery.id,
        "lead_id": delivery.lead_id,
        "full_name": delivery.full_name,
        "address": delivery.address,
        "city": delivery.city,
        "phone": delivery.phone,
        "email": delivery.email,
        "is_sent": delivery.is_sent,
        "sent_date": str(delivery.sent_date) if delivery.sent_date else None,
        "notes": delivery.notes,
        "created_at": str(delivery.created_at),
        "updated_at": str(delivery.updated_at),
    }


@router.post("/auto-create")
async def auto_create_deliveries(
    db: AsyncSession = Depends(get_db),
):
    """
    יוצר אוטומטית רשומות משלוח עבור לידים שהפכו ל"נסלק" ועדיין אין להם משלוח
    """
    result = await delivery_svc.auto_create_deliveries_for_sold_leads(db)
    await db.commit()
    return result
