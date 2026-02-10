"""
Collections service.
Manage debt collection attempts and link to Nedarim Plus.
"""
from datetime import date, datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Collection, Commitment, Student, Payment


async def create_collection(
    db: AsyncSession,
    student_id: int,
    amount: float,
    due_date: date,
    commitment_id: int | None = None,
    course_id: int | None = None,
    charge_day: int | None = None,
    installment_number: int | None = None,
    total_installments: int | None = None,
    notes: str | None = None,
) -> Collection:
    """Create a new collection record."""
    collection = Collection(
        student_id=student_id,
        commitment_id=commitment_id,
        course_id=course_id,
        amount=amount,
        due_date=due_date,
        charge_day=charge_day,
        installment_number=installment_number,
        total_installments=total_installments,
        notes=notes,
    )
    db.add(collection)
    await db.flush()
    return collection


async def create_collections_from_commitment(
    db: AsyncSession,
    commitment_id: int,
) -> list[Collection]:
    """
    Generate Collection records for all installments of a Commitment.
    Creates one Collection per scheduled payment.
    """
    stmt = select(Commitment).where(Commitment.id == commitment_id)
    result = await db.execute(stmt)
    commitment = result.scalar_one_or_none()
    
    if not commitment:
        raise ValueError(f"Commitment {commitment_id} not found")
    
    if not commitment.installments or commitment.installments < 1:
        # Single payment - no collections to generate
        return []
    
    collections = []
    charge_day = commitment.charge_day or 15  # Default to 15th of month
    start_date = date.today()
    
    for i in range(commitment.installments):
        # Calculate due date for each installment
        month_offset = (start_date.month + i - 1) % 12 + 1
        year_offset = start_date.year + (start_date.month + i - 1) // 12
        
        try:
            due = date(year_offset, month_offset, min(charge_day, 28))
        except ValueError:
            due = date(year_offset, month_offset, 28)
        
        collection = Collection(
            student_id=commitment.student_id,
            commitment_id=commitment.id,
            course_id=commitment.course_id,
            amount=float(commitment.monthly_amount),
            due_date=due,
            charge_day=charge_day,
            installment_number=i + 1,
            total_installments=commitment.installments,
            nedarim_subscription_id=commitment.nedarim_subscription_id,
        )
        db.add(collection)
        collections.append(collection)
    
    await db.flush()
    return collections


async def mark_collected(
    db: AsyncSession,
    collection_id: int,
    reference: str | None = None,
    payment_id: int | None = None,
    nedarim_donation_id: str | None = None,
) -> Collection | None:
    """Mark a collection as successfully collected."""
    stmt = select(Collection).where(Collection.id == collection_id)
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()
    if not collection:
        return None

    collection.status = "נגבה"
    collection.collected_at = datetime.now()
    collection.reference = reference
    collection.payment_id = payment_id
    collection.nedarim_donation_id = nedarim_donation_id
    await db.flush()
    return collection


async def mark_failed(
    db: AsyncSession,
    collection_id: int,
    error_message: str | None = None,
) -> Collection | None:
    """Mark a collection attempt as failed, increment attempts."""
    stmt = select(Collection).where(Collection.id == collection_id)
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()
    if not collection:
        return None

    collection.status = "נכשל"
    collection.attempts += 1
    if error_message:
        collection.notes = f"{collection.notes or ''}\n{datetime.now().isoformat()}: {error_message}".strip()
    await db.flush()
    return collection


async def retry_collection(
    db: AsyncSession,
    collection_id: int,
) -> Collection | None:
    """Reset a failed collection for retry."""
    stmt = select(Collection).where(Collection.id == collection_id)
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()
    if not collection:
        return None

    collection.status = "ממתין"
    await db.flush()
    return collection


async def get_student_collections(
    db: AsyncSession,
    student_id: int,
    status: str | None = None,
    limit: int = 50,
) -> list[Collection]:
    """Get all collections for a specific student."""
    stmt = (
        select(Collection)
        .where(Collection.student_id == student_id)
        .options(selectinload(Collection.commitment))
        .order_by(Collection.due_date.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(Collection.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_pending_collections(
    db: AsyncSession,
    student_id: int | None = None,
    limit: int = 50,
) -> list[Collection]:
    """Get pending collection records."""
    stmt = (
        select(Collection)
        .where(Collection.status == "ממתין")
        .options(selectinload(Collection.student), selectinload(Collection.commitment))
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
        .options(selectinload(Collection.student), selectinload(Collection.commitment))
        .order_by(Collection.due_date.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_collections_due_soon(
    db: AsyncSession,
    days: int = 7,
    limit: int = 100,
) -> list[Collection]:
    """Get collections due within the next N days."""
    future_date = date.today() + timedelta(days=days)
    stmt = (
        select(Collection)
        .where(
            Collection.status == "ממתין",
            Collection.due_date >= date.today(),
            Collection.due_date <= future_date,
        )
        .options(selectinload(Collection.student))
        .order_by(Collection.due_date.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_collection_summary(
    db: AsyncSession,
    student_id: int | None = None,
) -> dict:
    """Get collection statistics."""
    base_filter = []
    if student_id:
        base_filter.append(Collection.student_id == student_id)
    
    # Total pending
    stmt = select(func.sum(Collection.amount)).where(
        Collection.status == "ממתין",
        *base_filter
    )
    result = await db.execute(stmt)
    pending_amount = result.scalar() or 0
    
    # Total collected
    stmt = select(func.sum(Collection.amount)).where(
        Collection.status == "נגבה",
        *base_filter
    )
    result = await db.execute(stmt)
    collected_amount = result.scalar() or 0
    
    # Total failed
    stmt = select(func.sum(Collection.amount)).where(
        Collection.status == "נכשל",
        *base_filter
    )
    result = await db.execute(stmt)
    failed_amount = result.scalar() or 0
    
    # Overdue count
    stmt = select(func.count(Collection.id)).where(
        Collection.status == "ממתין",
        Collection.due_date < date.today(),
        *base_filter
    )
    result = await db.execute(stmt)
    overdue_count = result.scalar() or 0
    
    return {
        "pending_amount": float(pending_amount),
        "collected_amount": float(collected_amount),
        "failed_amount": float(failed_amount),
        "overdue_count": overdue_count,
    }
