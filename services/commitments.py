"""
Commitments service.
Manage standing orders / recurring payment commitments.
"""
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Commitment, Payment


async def create_commitment(
    db: AsyncSession,
    student_id: int,
    monthly_amount: float,
    course_id: int | None = None,
    total_amount: float | None = None,
    installments: int | None = None,
    charge_day: int | None = None,
    payment_method: str | None = None,
    reference: str | None = None,
    end_date: date | None = None,
) -> Commitment:
    """Create a new commitment (standing order)."""
    commitment = Commitment(
        student_id=student_id,
        course_id=course_id,
        monthly_amount=monthly_amount,
        total_amount=total_amount,
        installments=installments,
        charge_day=charge_day,
        payment_method=payment_method,
        reference=reference,
        end_date=end_date,
    )
    db.add(commitment)
    await db.flush()
    return commitment


async def get_commitment(db: AsyncSession, commitment_id: int) -> Commitment | None:
    stmt = select(Commitment).where(Commitment.id == commitment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_commitment_status(
    db: AsyncSession,
    commitment_id: int,
    status: str,
) -> Commitment | None:
    """Update commitment status (פעיל / מושהה / הסתיים / בוטל)."""
    stmt = select(Commitment).where(Commitment.id == commitment_id)
    result = await db.execute(stmt)
    commitment = result.scalar_one_or_none()
    if not commitment:
        return None
    commitment.status = status
    await db.flush()
    return commitment


async def get_student_commitments(
    db: AsyncSession,
    student_id: int,
    active_only: bool = True,
) -> list[Commitment]:
    """Get all commitments for a student."""
    stmt = select(Commitment).where(Commitment.student_id == student_id)
    if active_only:
        stmt = stmt.where(Commitment.status == "פעיל")
    stmt = stmt.order_by(Commitment.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_paid_total(db: AsyncSession, commitment_id: int) -> float:
    """Calculate total paid against a commitment."""
    stmt = select(func.sum(Payment.amount)).where(
        Payment.commitment_id == commitment_id,
        Payment.status == "שולם",
    )
    result = await db.execute(stmt)
    return float(result.scalar() or 0)
