"""
Expenses service.
Track expenses by vendor, course, campaign.
"""
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Expense


async def create_expense(
    db: AsyncSession,
    description: str,
    amount: float,
    category: str | None = None,
    vendor: str | None = None,
    expense_date: date | None = None,
    notes: str | None = None,
    course_id: int | None = None,
    campaign_id: int | None = None,
    payment_method: str | None = None,
    invoice_file: str | None = None,
) -> Expense:
    """Record a new expense."""
    expense = Expense(
        description=description,
        category=category,
        amount=amount,
        vendor=vendor,
        expense_date=expense_date or date.today(),
        notes=notes,
        course_id=course_id,
        campaign_id=campaign_id,
        payment_method=payment_method,
        invoice_file=invoice_file,
    )
    db.add(expense)
    await db.flush()
    return expense


async def list_expenses(
    db: AsyncSession,
    course_id: int | None = None,
    campaign_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Expense]:
    """List expenses with filters."""
    stmt = select(Expense).order_by(Expense.expense_date.desc()).limit(limit).offset(offset)
    if course_id:
        stmt = stmt.where(Expense.course_id == course_id)
    if campaign_id:
        stmt = stmt.where(Expense.campaign_id == campaign_id)
    if from_date:
        stmt = stmt.where(Expense.expense_date >= from_date)
    if to_date:
        stmt = stmt.where(Expense.expense_date <= to_date)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def total_expenses(
    db: AsyncSession,
    course_id: int | None = None,
    campaign_id: int | None = None,
) -> float:
    """Get total expenses with optional filter."""
    stmt = select(func.sum(Expense.amount))
    if course_id:
        stmt = stmt.where(Expense.course_id == course_id)
    if campaign_id:
        stmt = stmt.where(Expense.campaign_id == campaign_id)
    result = await db.execute(stmt)
    return float(result.scalar() or 0)
