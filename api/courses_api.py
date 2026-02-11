"""
Courses API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import courses as course_svc
from services import lecturers as lecturer_svc
from services import audit_logs
from .dependencies import require_entity_access

router = APIRouter(tags=["courses"])


# ── Schemas ──────────────────────────────────────────
class CourseCreate(BaseModel):
    name: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    semester: str | None = None
    total_sessions: int | None = None
    price: float | None = None
    payments_count: int = 1
    is_active: bool = True


class CourseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    semester: str | None = None
    total_sessions: int | None = None
    price: float | None = None
    payments_count: int | None = None
    is_active: bool | None = None


# ── Endpoints ────────────────────────────────────────
@router.get("/")
async def list_courses(
    user = Depends(require_entity_access("courses", "view")),
    db: AsyncSession = Depends(get_db)
):
    items = await course_svc.get_courses(db)
    return [
        {
            "id": c.id,
            "name": c.name,
            "total_sessions": c.total_sessions,
            "price": float(c.price) if c.price else None,
            "payments_count": c.payments_count,
            "is_active": c.is_active
        }
        for c in items
    ]


@router.get("/{course_id}")
async def get_course(
    course_id: int,
    user = Depends(require_entity_access("courses", "view")),
    db: AsyncSession = Depends(get_db)
):
    course = await course_svc.get_course_with_modules(db, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "semester": course.semester,
        "start_date": course.start_date.isoformat() if course.start_date else None,
        "end_date": course.end_date.isoformat() if course.end_date else None,
        "total_sessions": course.total_sessions,
        "price": float(course.price) if course.price else None,
        "payments_count": course.payments_count,
        "is_active": course.is_active,
        "modules": [
            {
                "id": m.id,
                "name": m.name,
                "module_order": m.module_order,
                "sessions_count": m.sessions_count,
            }
            for m in sorted(course.modules, key=lambda x: x.module_order)
        ],
    }


@router.get("/{course_id}/entry-points")
async def get_entry_points(
    course_id: int,
    user = Depends(require_entity_access("courses", "view")),
    db: AsyncSession = Depends(get_db)
):
    entries = await course_svc.get_entry_points(db, course_id)
    return entries


@router.get("/{course_id}/remaining")
async def calculate_remaining(
    course_id: int,
    from_module: int = Query(1),
    user = Depends(require_entity_access("courses", "view")),
    db: AsyncSession = Depends(get_db),
):
    result = await course_svc.calculate_remaining(db, course_id, from_module)
    return result


@router.post("/")
async def create_course(
    data: CourseCreate,
    request: Request,
    user = Depends(require_entity_access("courses", "create")),
    db: AsyncSession = Depends(get_db)
):
    course = await course_svc.create_course(db, **data.model_dump())
    await db.commit()
    
    await audit_logs.log_create(
        db=db,
        user=user,
        entity_type="courses",
        entity_id=course.id,
        description=f"נוצר קורס: {data.name}",
        request=request,
    )
    
    return {"id": course.id, "name": course.name}


@router.patch("/{course_id}")
async def update_course(
    course_id: int,
    data: CourseUpdate,
    request: Request,
    user = Depends(require_entity_access("courses", "edit")),
    db: AsyncSession = Depends(get_db)
):
    update_data = data.model_dump(exclude_unset=True)
    print(f"[DEBUG] Updating course {course_id} with data: {update_data}")
    
    course = await course_svc.update_course(db, course_id, **update_data)
    if not course:
        raise HTTPException(404, "Course not found")
    await db.commit()
    
    print(f"[DEBUG] Course after update - price: {course.price}, payments_count: {course.payments_count}")
    
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="courses",
        entity_id=course_id,
        description=f"עודכן קורס: {course.name}",
        changes=update_data,
        request=request,
    )
    
    return {"id": course.id, "name": course.name, "price": float(course.price) if course.price else None, "payments_count": course.payments_count}


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    request: Request,
    user = Depends(require_entity_access("courses", "delete")),
    db: AsyncSession = Depends(get_db)
):
    success = await course_svc.delete_course(db, course_id)
    if not success:
        raise HTTPException(404, "Course not found")
    await db.commit()
    
    await audit_logs.log_delete(
        db=db,
        user=user,
        entity_type="courses",
        entity_id=course_id,
        description="קורס בוטל",
        request=request,
    )
    
    return {"success": True}


@router.get("/lecturers")
async def list_lecturers(
    user = Depends(require_entity_access("lecturers", "view")),
    db: AsyncSession = Depends(get_db)
):
    """Get all lecturers - used by TracksPage."""
    items = await lecturer_svc.get_lecturers(db)
    return [{"id": lec.id, "name": lec.name} for lec in items]
