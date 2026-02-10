"""
Payments service.
"""
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Payment, Student


async def create_payment(
    db: AsyncSession,
    student_id: int | None = None,
    lead_id: int | None = None,
    amount: float = 0,
    payment_method: str | None = None,
    reference: str | None = None,
) -> Payment:
    """Record a payment."""
    payment = Payment(
        student_id=student_id,
        lead_id=lead_id,
        amount=amount,
        payment_date=date.today(),
        payment_method=payment_method,
        status="שולם",
        reference=reference,
    )
    db.add(payment)
    await db.flush()

    # Update student total_paid
    if student_id:
        stmt = select(Student).where(Student.id == student_id)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()
        if student:
            student.total_paid = (student.total_paid or 0) + amount
            if student.total_price and student.total_paid >= student.total_price:
                student.payment_status = "שולם"
            await db.flush()

    return payment


async def get_student_balance(db: AsyncSession, student_id: int) -> dict:
    """Get payment balance for a student."""
    stmt = select(Student).where(Student.id == student_id)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    if not student:
        return {"error": "Student not found"}

    return {
        "total_price": float(student.total_price or 0),
        "total_paid": float(student.total_paid or 0),
        "balance": float((student.total_price or 0) - (student.total_paid or 0)),
        "status": student.payment_status,
    }
