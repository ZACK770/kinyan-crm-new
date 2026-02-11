"""
Lecturers service.
Manage course lecturers/instructors.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lecturer


async def get_lecturers(db: AsyncSession) -> list[Lecturer]:
    """Get all lecturers."""
    stmt = select(Lecturer).order_by(Lecturer.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_lecturer(
    db: AsyncSession,
    name: str,
    specialty: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    notes: str | None = None,
) -> Lecturer:
    """Create a new lecturer."""
    lecturer = Lecturer(
        name=name,
        specialty=specialty,
        phone=phone,
        email=email,
        notes=notes,
    )
    db.add(lecturer)
    await db.flush()
    return lecturer


async def update_lecturer(
    db: AsyncSession,
    lecturer_id: int,
    **kwargs,
) -> Lecturer | None:
    """Update lecturer fields."""
    stmt = select(Lecturer).where(Lecturer.id == lecturer_id)
    result = await db.execute(stmt)
    lecturer = result.scalar_one_or_none()
    if not lecturer:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(lecturer, key):
            setattr(lecturer, key, value)
    await db.flush()
    return lecturer
