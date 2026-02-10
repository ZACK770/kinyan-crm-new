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
        "email": s.email,
        "status": s.status,
        "enrollments": [
            {
                "id": e.id,
                "course_id": e.course_id,
                "status": e.status,
                "current_module": e.current_module,
                "sessions_remaining": e.sessions_remaining,
            }
            for e in dashboard["enrollments"]
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
