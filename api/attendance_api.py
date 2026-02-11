"""
Attendance API endpoints.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import attendance as attendance_svc
from .dependencies import require_entity_access

router = APIRouter()


class AttendanceRecord(BaseModel):
    student_id: int
    module_id: int
    is_present: bool = True
    assignment_done: bool = False
    score: int | None = None
    lecturer_id: int | None = None
    attendance_date: date | None = None


@router.post("/")
async def record_attendance(
    data: AttendanceRecord,
    user = Depends(require_entity_access("attendance", "create")),
    db: AsyncSession = Depends(get_db)
):
    record = await attendance_svc.record_attendance(db, **data.model_dump())
    await db.commit()
    return {"id": record.id, "is_present": record.is_present}


@router.get("/student/{student_id}")
async def get_student_attendance(
    student_id: int,
    course_id: int | None = Query(None),
    user = Depends(require_entity_access("attendance", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await attendance_svc.get_student_attendance(db, student_id, course_id=course_id)
    return [
        {
            "id": a.id,
            "module_id": a.module_id,
            "date": str(a.attendance_date),
            "is_present": a.is_present,
            "assignment_done": a.assignment_done,
            "score": a.score,
        }
        for a in items
    ]


@router.get("/module/{module_id}/stats")
async def module_stats(module_id: int, db: AsyncSession = Depends(get_db)):
    return await attendance_svc.get_module_attendance_rate(db, module_id)
