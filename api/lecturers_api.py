"""
Lecturers API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import lecturers as lecturer_svc
from services import audit_logs
from .dependencies import require_entity_access

router = APIRouter(tags=["lecturers"])


# ── Schemas ──────────────────────────────────────────
class LecturerCreate(BaseModel):
    name: str
    specialty: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class LecturerUpdate(BaseModel):
    name: str | None = None
    specialty: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


# ── Endpoints ────────────────────────────────────────
@router.get("/")
async def list_lecturers(
    user = Depends(require_entity_access("lecturers", "view")),
    db: AsyncSession = Depends(get_db)
):
    """Get all lecturers."""
    items = await lecturer_svc.get_lecturers(db)
    return [
        {
            "id": lec.id,
            "name": lec.name,
            "specialty": lec.specialty,
            "phone": lec.phone,
            "email": lec.email,
            "notes": lec.notes,
            "created_at": lec.created_at.isoformat() if lec.created_at else None,
        }
        for lec in items
    ]


@router.get("/{lecturer_id}")
async def get_lecturer(
    lecturer_id: int,
    user = Depends(require_entity_access("lecturers", "view")),
    db: AsyncSession = Depends(get_db)
):
    """Get a single lecturer by ID."""
    from sqlalchemy import select
    from db.models import Lecturer
    
    stmt = select(Lecturer).where(Lecturer.id == lecturer_id)
    result = await db.execute(stmt)
    lecturer = result.scalar_one_or_none()
    
    if not lecturer:
        raise HTTPException(404, "Lecturer not found")
    
    return {
        "id": lecturer.id,
        "name": lecturer.name,
        "specialty": lecturer.specialty,
        "phone": lecturer.phone,
        "email": lecturer.email,
        "notes": lecturer.notes,
        "created_at": lecturer.created_at.isoformat() if lecturer.created_at else None,
    }


@router.post("/")
async def create_lecturer(
    data: LecturerCreate,
    request: Request,
    user = Depends(require_entity_access("lecturers", "create")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new lecturer."""
    lecturer = await lecturer_svc.create_lecturer(
        db,
        name=data.name,
        specialty=data.specialty,
        phone=data.phone,
        email=data.email,
        notes=data.notes,
    )
    await db.commit()
    
    await audit_logs.log_create(
        db=db,
        user=user,
        entity_type="lecturers",
        entity_id=lecturer.id,
        description=f"נוצר מרצה: {data.name}",
        request=request,
    )
    
    return {"id": lecturer.id, "name": lecturer.name}


@router.patch("/{lecturer_id}")
async def update_lecturer(
    lecturer_id: int,
    data: LecturerUpdate,
    request: Request,
    user = Depends(require_entity_access("lecturers", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """Update a lecturer."""
    update_data = data.model_dump(exclude_unset=True)
    lecturer = await lecturer_svc.update_lecturer(db, lecturer_id, **update_data)
    
    if not lecturer:
        raise HTTPException(404, "Lecturer not found")
    
    await db.commit()
    
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="lecturers",
        entity_id=lecturer_id,
        description=f"עודכן מרצה: {lecturer.name}",
        changes=update_data,
        request=request,
    )
    
    return {"id": lecturer.id, "name": lecturer.name}


@router.delete("/{lecturer_id}")
async def delete_lecturer(
    lecturer_id: int,
    request: Request,
    user = Depends(require_entity_access("lecturers", "delete")),
    db: AsyncSession = Depends(get_db)
):
    """Delete a lecturer (soft delete if has relations, hard delete otherwise)."""
    from sqlalchemy import select, delete as sql_delete
    from db.models import Lecturer, CourseModule, CourseTrack, Exam, Attendance
    
    stmt = select(Lecturer).where(Lecturer.id == lecturer_id)
    result = await db.execute(stmt)
    lecturer = result.scalar_one_or_none()
    
    if not lecturer:
        raise HTTPException(404, "Lecturer not found")
    
    # Check if lecturer has any relations
    has_modules = (await db.execute(select(CourseModule).where(CourseModule.lecturer_id == lecturer_id).limit(1))).first()
    has_tracks = (await db.execute(select(CourseTrack).where(CourseTrack.lecturer_id == lecturer_id).limit(1))).first()
    has_exams = (await db.execute(select(Exam).where(Exam.lecturer_id == lecturer_id).limit(1))).first()
    has_attendance = (await db.execute(select(Attendance).where(Attendance.lecturer_id == lecturer_id).limit(1))).first()
    
    if has_modules or has_tracks or has_exams or has_attendance:
        raise HTTPException(400, "לא ניתן למחוק מרצה המקושר למודולים, מסלולים, מבחנים או נוכחות")
    
    # Hard delete if no relations
    await db.execute(sql_delete(Lecturer).where(Lecturer.id == lecturer_id))
    await db.commit()
    
    await audit_logs.log_delete(
        db=db,
        user=user,
        entity_type="lecturers",
        entity_id=lecturer_id,
        description=f"נמחק מרצה: {lecturer.name}",
        request=request,
    )
    
    return {"success": True}
