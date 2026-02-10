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


async def create_course(db: AsyncSession, **kwargs) -> Course:
    """Create a new course."""
    course = Course(
        name=kwargs.get("name", ""),
        description=kwargs.get("description"),
        start_date=kwargs.get("start_date"),
        end_date=kwargs.get("end_date"),
        semester=kwargs.get("semester"),
        syllabus_url=kwargs.get("syllabus_url"),
        website_url=kwargs.get("website_url"),
        zoom_url=kwargs.get("zoom_url"),
        is_active=kwargs.get("is_active", True),
    )
    db.add(course)
    await db.flush()
    return course


async def update_course(db: AsyncSession, course_id: int, **kwargs) -> Course | None:
    """Update course fields."""
    stmt = select(Course).where(Course.id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    if not course:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(course, key):
            setattr(course, key, value)

    await db.flush()
    return course


async def delete_course(db: AsyncSession, course_id: int) -> bool:
    """Soft delete (deactivate) a course."""
    stmt = select(Course).where(Course.id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    if not course:
        return False

    course.is_active = False
    await db.flush()
    return True


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
