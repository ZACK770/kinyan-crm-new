"""
Collections API endpoints.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import collections as collection_svc
from .dependencies import require_entity_access

router = APIRouter()


class CollectionCreate(BaseModel):
    student_id: int
    amount: float
    due_date: date
    commitment_id: int | None = None
    course_id: int | None = None
    charge_day: int | None = None
    installment_number: int | None = None
    total_installments: int | None = None
    notes: str | None = None


class CollectSuccess(BaseModel):
    reference: str | None = None
    payment_id: int | None = None
    nedarim_donation_id: str | None = None


class MarkFailed(BaseModel):
    error_message: str | None = None


def format_collection(c, include_student: bool = False, include_commitment: bool = False) -> dict:
    """Format collection for API response."""
    result = {
        "id": c.id,
        "student_id": c.student_id,
        "commitment_id": c.commitment_id,
        "payment_id": c.payment_id,
        "course_id": c.course_id,
        "amount": float(c.amount),
        "due_date": str(c.due_date),
        "charge_day": c.charge_day,
        "installment_number": c.installment_number,
        "total_installments": c.total_installments,
        "status": c.status,
        "attempts": c.attempts,
        "collected_at": str(c.collected_at) if c.collected_at else None,
        "reference": c.reference,
        "notes": c.notes,
        "nedarim_donation_id": c.nedarim_donation_id,
        "nedarim_subscription_id": c.nedarim_subscription_id,
        "created_at": str(c.created_at),
    }
    
    if include_student and hasattr(c, 'student') and c.student:
        result["student"] = {
            "id": c.student.id,
            "full_name": c.student.full_name,
            "phone": c.student.phone,
        }
    
    if include_commitment and hasattr(c, 'commitment') and c.commitment:
        result["commitment"] = {
            "id": c.commitment.id,
            "monthly_amount": float(c.commitment.monthly_amount),
            "installments": c.commitment.installments,
            "status": c.commitment.status,
        }
    
    return result


@router.post("/")
async def create_collection(
    data: CollectionCreate,
    user = Depends(require_entity_access("collections", "create")),
    db: AsyncSession = Depends(get_db)
):
    collection = await collection_svc.create_collection(db, **data.model_dump())
    await db.commit()
    return {"id": collection.id, "status": collection.status}


@router.get("/pending")
async def get_pending(
    student_id: int | None = Query(None),
    limit: int = Query(50, le=200),
    user = Depends(require_entity_access("collections", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await collection_svc.get_pending_collections(db, student_id=student_id, limit=limit)
    return [format_collection(c, include_student=True, include_commitment=True) for c in items]


@router.get("/overdue")
async def get_overdue(
    limit: int = Query(100, le=500),
    user = Depends(require_entity_access("collections", "view")),
    db: AsyncSession = Depends(get_db)
):
    items = await collection_svc.get_overdue_collections(db, limit=limit)
    return [format_collection(c, include_student=True, include_commitment=True) for c in items]


@router.get("/due-soon")
async def get_due_soon(
    days: int = Query(7, le=30),
    limit: int = Query(100, le=500),
    user = Depends(require_entity_access("collections", "view")),
    db: AsyncSession = Depends(get_db)
):
    """Get collections due within the next N days."""
    items = await collection_svc.get_collections_due_soon(db, days=days, limit=limit)
    return [format_collection(c, include_student=True) for c in items]


@router.get("/summary")
async def get_summary(
    student_id: int | None = Query(None),
    user = Depends(require_entity_access("collections", "view")),
    db: AsyncSession = Depends(get_db)
):
    """Get collection statistics."""
    return await collection_svc.get_collection_summary(db, student_id=student_id)


@router.get("/student/{student_id}")
async def get_student_collections(
    student_id: int,
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    user = Depends(require_entity_access("collections", "view")),
    db: AsyncSession = Depends(get_db)
):
    """Get all collections for a specific student."""
    items = await collection_svc.get_student_collections(db, student_id=student_id, status=status, limit=limit)
    return [format_collection(c, include_commitment=True) for c in items]


@router.post("/{collection_id}/collected")
async def mark_collected(
    collection_id: int,
    data: CollectSuccess,
    user = Depends(require_entity_access("collections", "edit")),
    db: AsyncSession = Depends(get_db)
):
    collection = await collection_svc.mark_collected(
        db, 
        collection_id, 
        reference=data.reference,
        payment_id=data.payment_id,
        nedarim_donation_id=data.nedarim_donation_id,
    )
    if not collection:
        raise HTTPException(404, "Collection not found")
    await db.commit()
    return {"id": collection.id, "status": collection.status}


@router.post("/{collection_id}/failed")
async def mark_failed(
    collection_id: int,
    data: MarkFailed = None,
    user = Depends(require_entity_access("collections", "edit")),
    db: AsyncSession = Depends(get_db)
):
    error_message = data.error_message if data else None
    collection = await collection_svc.mark_failed(db, collection_id, error_message=error_message)
    if not collection:
        raise HTTPException(404, "Collection not found")
    await db.commit()
    return {"id": collection.id, "status": collection.status, "attempts": collection.attempts}


@router.post("/{collection_id}/retry")
async def retry_collection(
    collection_id: int,
    user = Depends(require_entity_access("collections", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """Reset a failed collection for retry."""
    collection = await collection_svc.retry_collection(db, collection_id)
    if not collection:
        raise HTTPException(404, "Collection not found")
    await db.commit()
    return {"id": collection.id, "status": collection.status}


@router.post("/commitment/{commitment_id}/generate")
async def generate_from_commitment(
    commitment_id: int,
    user = Depends(require_entity_access("collections", "create")),
    db: AsyncSession = Depends(get_db)
):
    """Generate collection records for all installments of a commitment."""
    try:
        collections = await collection_svc.create_collections_from_commitment(db, commitment_id)
        await db.commit()
        return {
            "commitment_id": commitment_id,
            "collections_created": len(collections),
            "collection_ids": [c.id for c in collections],
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
