"""
Collections service.
Manage debt collection attempts.
"""
from datetime import date, datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Collection


async def create_collection(
    db: AsyncSession,
    student_id: int,
    amount: float,
    due_date: date,
    commitment_id: int | None = None,
    notes: str | None = None,
) -> Collection:
    """Create a new collection record."""
    collection = Collection(
        student_id=student_id,
        commitment_id=commitment_id,
        amount=amount,
        due_date=due_date,
        notes=notes,
    )
    db.add(collection)
    await db.flush()
    return collection


async def mark_collected(
    db: AsyncSession,
    collection_id: int,
    reference: str | None = None,
) -> Collection | None:
    """Mark a collection as successfully collected."""
    stmt = select(Collection).where(Collection.id == collection_id)
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()
    if not collection:
        return None

    collection.status = "נגבה"
    collection.collected_at = func.now()
    collection.reference = reference
    await db.flush()
    return collection


async def mark_failed(
    db: AsyncSession,
    collection_id: int,
) -> Collection | None:
    """Mark a collection attempt as failed, increment attempts."""
    stmt = select(Collection).where(Collection.id == collection_id)
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()
    if not collection:
        return None

    collection.status = "נכשל"
    collection.attempts += 1
    await db.flush()
    return collection


async def get_pending_collections(
    db: AsyncSession,
    student_id: int | None = None,
    limit: int = 50,
) -> list[Collection]:
    """Get pending collection records."""
    stmt = (
        select(Collection)
        .where(Collection.status == "ממתין")
        .order_by(Collection.due_date.asc())
        .limit(limit)
    )
    if student_id:
        stmt = stmt.where(Collection.student_id == student_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_overdue_collections(db: AsyncSession, limit: int = 100) -> list[Collection]:
    """Get overdue collections (past due_date and still pending)."""
    stmt = (
        select(Collection)
        .where(
            Collection.status == "ממתין",
            Collection.due_date < date.today(),
        )
        .order_by(Collection.due_date.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
