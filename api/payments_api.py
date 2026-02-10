"""
Payments & Commitments API endpoints.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import payments as payment_svc
from services import commitments as commitment_svc
from .dependencies import require_entity_access

router = APIRouter()


# ── Schemas ──────────────────────────────────────────
class PaymentCreate(BaseModel):
    student_id: int | None = None
    lead_id: int | None = None
    course_id: int | None = None
    commitment_id: int | None = None
    amount: float
    payment_method: str | None = None
    reference: str | None = None
    currency: str | None = "₪"
    transaction_type: str | None = None
    installments: int | None = None
    charge_day: int | None = None


class CommitmentCreate(BaseModel):
    student_id: int
    monthly_amount: float
    course_id: int | None = None
    total_amount: float | None = None
    installments: int | None = None
    charge_day: int | None = None
    payment_method: str | None = None
    reference: str | None = None
    end_date: date | None = None


class CommitmentStatusUpdate(BaseModel):
    status: str  # פעיל / מושהה / הסתיים / בוטל


# ── Payments ─────────────────────────────────────────
@router.post("/payments")
async def create_payment(
    data: PaymentCreate,
    user = Depends(require_entity_access("payments", "create")),
    db: AsyncSession = Depends(get_db)
):
    payment = await payment_svc.create_payment(db, **data.model_dump())
    await db.commit()
    return {"id": payment.id, "amount": float(payment.amount), "status": payment.status}


@router.get("/payments/student/{student_id}")
async def get_student_balance(
    student_id: int,
    user = Depends(require_entity_access("payments", "view")),
    db: AsyncSession = Depends(get_db)
):
    return await payment_svc.get_student_balance(db, student_id)


# ── Commitments ──────────────────────────────────────
@router.post("/commitments")
async def create_commitment(
    data: CommitmentCreate,
    user = Depends(require_entity_access("payments", "create")),
    db: AsyncSession = Depends(get_db)
):
    commitment = await commitment_svc.create_commitment(db, **data.model_dump())
    await db.commit()
    return {"id": commitment.id, "status": commitment.status}


@router.get("/commitments/student/{student_id}")
async def get_student_commitments(
    student_id: int,
    active_only: bool = Query(True),
    user = Depends(require_entity_access("payments", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await commitment_svc.get_student_commitments(db, student_id, active_only=active_only)
    return [
        {
            "id": c.id,
            "monthly_amount": float(c.monthly_amount),
            "status": c.status,
            "installments": c.installments,
            "created_at": str(c.created_at),
        }
        for c in items
    ]


@router.patch("/commitments/{commitment_id}/status")
async def update_commitment_status(
    commitment_id: int,
    data: CommitmentStatusUpdate,
    user = Depends(require_entity_access("payments", "edit")),
    db: AsyncSession = Depends(get_db),
):
    commitment = await commitment_svc.update_commitment_status(db, commitment_id, data.status)
    if not commitment:
        raise HTTPException(404, "Commitment not found")
    await db.commit()
    return {"id": commitment.id, "status": commitment.status}
