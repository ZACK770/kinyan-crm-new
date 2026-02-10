"""
Course management service.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Course, CourseModule


async def get_courses(db: AsyncSession, active_only: bool = True) -> list[Course]:
    """Get all courses."""
    stmt = select(Course).order_by(Course.name)
    if active_only:
        stmt = stmt.where(Course.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_course_with_modules(db: AsyncSession, course_id: int) -> Course | None:
    """Get a course with all its modules."""
    stmt = (
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.modules))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_entry_points(db: AsyncSession, course_id: int) -> list[dict]:
    """Get possible entry points for a course (each module is an entry point)."""
    stmt = (
        select(CourseModule)
        .where(CourseModule.course_id == course_id)
        .order_by(CourseModule.module_order)
    )
    result = await db.execute(stmt)
    modules = result.scalars().all()

    total_sessions = sum(m.sessions_count or 0 for m in modules)
    entries = []
    remaining = total_sessions

    for m in modules:
        entries.append({
            "module_id": m.id,
            "module_order": m.module_order,
            "name": m.name,
            "sessions_count": m.sessions_count,
            "sessions_remaining": remaining,
            "hours_remaining": float(sum(
                (mod.hours_estimate or 0) for mod in modules if mod.module_order >= m.module_order
            )),
        })
        remaining -= (m.sessions_count or 0)

    return entries


async def calculate_remaining(db: AsyncSession, course_id: int, from_module: int) -> dict:
    """Calculate remaining sessions/hours from a given module entry point."""
    stmt = (
        select(CourseModule)
        .where(CourseModule.course_id == course_id, CourseModule.module_order >= from_module)
        .order_by(CourseModule.module_order)
    )
    result = await db.execute(stmt)
    modules = result.scalars().all()

    sessions = sum(m.sessions_count or 0 for m in modules)
    hours = sum(float(m.hours_estimate or 0) for m in modules)

    return {
        "modules_remaining": len(modules),
        "sessions_remaining": sessions,
        "hours_remaining": round(hours, 1),
        "estimated_days": int(sessions * 3.5),
    }
