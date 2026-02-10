"""
Courses API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import courses as course_svc
from .dependencies import require_entity_access

router = APIRouter(tags=["courses"])


@router.get("/")
async def list_courses(
    user = Depends(require_entity_access("courses", "view")),
    db: AsyncSession = Depends(get_db)
):
    items = await course_svc.get_courses(db)
    return [
        {"id": c.id, "name": c.name, "total_sessions": c.total_sessions, "is_active": c.is_active}
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
        "total_sessions": course.total_sessions,
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
