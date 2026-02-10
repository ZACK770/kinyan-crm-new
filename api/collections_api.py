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
    notes: str | None = None


class CollectSuccess(BaseModel):
    reference: str | None = None


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
    return [
        {
            "id": c.id,
            "student_id": c.student_id,
            "amount": float(c.amount),
            "due_date": str(c.due_date),
            "attempts": c.attempts,
        }
        for c in items
    ]


@router.get("/overdue")
async def get_overdue(
    limit: int = Query(100, le=500),
    user = Depends(require_entity_access("collections", "view")),
    db: AsyncSession = Depends(get_db)
):
    items = await collection_svc.get_overdue_collections(db, limit=limit)
    return [
        {
            "id": c.id,
            "student_id": c.student_id,
            "amount": float(c.amount),
            "due_date": str(c.due_date),
            "attempts": c.attempts,
        }
        for c in items
    ]


@router.post("/{collection_id}/collected")
async def mark_collected(
    collection_id: int,
    data: CollectSuccess,
    user = Depends(require_entity_access("collections", "edit")),
    db: AsyncSession = Depends(get_db)
):
    collection = await collection_svc.mark_collected(db, collection_id, data.reference)
    if not collection:
        raise HTTPException(404, "Collection not found")
    await db.commit()
    return {"id": collection.id, "status": collection.status}


@router.post("/{collection_id}/failed")
async def mark_failed(
    collection_id: int,
    user = Depends(require_entity_access("collections", "edit")),
    db: AsyncSession = Depends(get_db)
):
    collection = await collection_svc.mark_failed(db, collection_id)
    if not collection:
        raise HTTPException(404, "Collection not found")
    await db.commit()
    return {"id": collection.id, "status": collection.status, "attempts": collection.attempts}
