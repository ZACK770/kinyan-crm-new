"""
Expenses API endpoints.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import expenses as expense_svc
from .dependencies import require_entity_access

router = APIRouter()


class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: str | None = None
    vendor: str | None = None
    expense_date: date | None = None
    notes: str | None = None
    course_id: int | None = None
    campaign_id: int | None = None
    payment_method: str | None = None
    invoice_file: str | None = None


@router.get("/")
async def list_expenses(
    course_id: int | None = Query(None),
    campaign_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user = Depends(require_entity_access("expenses", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await expense_svc.list_expenses(
        db, course_id=course_id, campaign_id=campaign_id,
        from_date=from_date, to_date=to_date, limit=limit, offset=offset,
    )
    return [
        {
            "id": e.id,
            "description": e.description,
            "category": e.category,
            "amount": float(e.amount) if e.amount else 0,
            "expense_date": str(e.expense_date) if e.expense_date else None,
            "vendor": e.vendor,
            "notes": e.notes,
            "course_id": e.course_id,
            "campaign_id": e.campaign_id,
            "created_at": str(e.created_at) if e.created_at else None,
        }
        for e in items
    ]


@router.post("/")
async def create_expense(
    data: ExpenseCreate,
    user = Depends(require_entity_access("expenses", "create")),
    db: AsyncSession = Depends(get_db)
):
    expense = await expense_svc.create_expense(db, **data.model_dump())
    await db.commit()
    return {"id": expense.id, "amount": float(expense.amount)}


@router.get("/total")
async def total_expenses(
    course_id: int | None = Query(None),
    campaign_id: int | None = Query(None),
    user = Depends(require_entity_access("expenses", "view")),
    db: AsyncSession = Depends(get_db),
):
    total = await expense_svc.total_expenses(db, course_id=course_id, campaign_id=campaign_id)
    return {"total": total}
