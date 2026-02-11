"""
Students API endpoints.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import students as student_svc
from .dependencies import require_entity_access

router = APIRouter(tags=["students"])


# ── Schemas ──────────────────────────────────────────
class ConvertLead(BaseModel):
    lead_id: int


class EnrollStudent(BaseModel):
    course_id: int
    entry_module_order: int = 1
    start_date: date | None = None


class UpdateProgress(BaseModel):
    current_module: int


# ── Endpoints ────────────────────────────────────────
@router.get("/")
async def list_students(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user = Depends(require_entity_access("students", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await student_svc.list_students(db, status=status, limit=limit, offset=offset)
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "phone": s.phone,
            "status": s.status,
            "created_at": str(s.created_at),
        }
        for s in items
    ]


@router.post("/convert")
async def convert_lead(
    data: ConvertLead,
    user = Depends(require_entity_access("students", "create")),
    db: AsyncSession = Depends(get_db)
):
    try:
        student = await student_svc.create_from_lead(db, data.lead_id)
        await db.commit()
        return {"id": student.id, "full_name": student.full_name}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{student_id}")
async def get_student(
    student_id: int,
    user = Depends(require_entity_access("students", "view")),
    db: AsyncSession = Depends(get_db)
):
    dashboard = await student_svc.get_student_dashboard(db, student_id)
    if not dashboard:
        raise HTTPException(404, "Student not found")
    s = dashboard["student"]
    return {
        "id": s.id,
        "full_name": s.full_name,
        "phone": s.phone,
        "phone2": s.phone2,
        "email": s.email,
        "address": s.address,
        "city": s.city,
        "id_number": s.id_number,
        "notes": s.notes,
        "status": s.status,
        "approved_terms": s.approved_terms,
        "nedarim_payer_id": s.nedarim_payer_id,
        "lead_id": s.lead_id,
        "total_price": float(s.total_price) if s.total_price else None,
        "total_paid": float(s.total_paid) if s.total_paid else 0,
        "payment_status": s.payment_status,
        "shipping_status": s.shipping_status,
        "created_at": str(s.created_at),
        "enrollments": [
            {
                "id": e.id,
                "course_id": e.course_id,
                "course_name": e.course.name if e.course else None,
                "status": e.status,
                "current_module": e.current_module,
                "sessions_remaining": e.sessions_remaining,
                "enrollment_date": str(e.enrollment_date) if e.enrollment_date else None,
            }
            for e in dashboard["enrollments"]
        ],
        "payments": [
            {
                "id": p.id,
                "amount": float(p.amount),
                "status": p.status,
                "payment_date": str(p.payment_date) if p.payment_date else None,
                "payment_method": p.payment_method,
                "transaction_type": p.transaction_type,
                "reference": p.reference,
            }
            for p in dashboard["payments"]
        ],
        "collections": [
            {
                "id": c.id,
                "amount": float(c.amount),
                "due_date": str(c.due_date),
                "status": c.status,
                "installment_number": c.installment_number,
                "total_installments": c.total_installments,
                "collected_at": str(c.collected_at) if c.collected_at else None,
                "attempts": c.attempts,
            }
            for c in dashboard["collections"]
        ],
        "commitments": [
            {
                "id": cm.id,
                "monthly_amount": float(cm.monthly_amount),
                "total_amount": float(cm.total_amount) if cm.total_amount else None,
                "installments": cm.installments,
                "charge_day": cm.charge_day,
                "status": cm.status,
                "nedarim_subscription_id": cm.nedarim_subscription_id,
            }
            for cm in dashboard["commitments"]
        ],
    }


@router.post("/{student_id}/enroll")
async def enroll(
    student_id: int,
    data: EnrollStudent,
    user = Depends(require_entity_access("students", "edit")),
    db: AsyncSession = Depends(get_db)
):
    try:
        enrollment = await student_svc.enroll_in_course(
            db, student_id, data.course_id, data.entry_module_order, data.start_date
        )
        await db.commit()
        return {
            "id": enrollment.id,
            "sessions_remaining": enrollment.sessions_remaining,
            "estimated_finish": str(enrollment.estimated_finish),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.patch("/{student_id}/enrollments/{enrollment_id}/progress")
async def update_progress(
    student_id: int,
    enrollment_id: int,
    data: UpdateProgress,
    user = Depends(require_entity_access("students", "edit")),
    db: AsyncSession = Depends(get_db)
):
    enrollment = await student_svc.update_progress(db, enrollment_id, data.current_module)
    if not enrollment:
        raise HTTPException(404, "Enrollment not found")
    await db.commit()
    return {
        "current_module": enrollment.current_module,
        "sessions_remaining": enrollment.sessions_remaining,
        "status": enrollment.status,
    }
