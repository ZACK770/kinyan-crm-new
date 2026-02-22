"""
Sales management service.
Salespeople dashboard, tasks, lead assignment.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Salesperson, SalesTask, Lead, User


async def get_active_salespeople(db: AsyncSession) -> list[Salesperson]:
    """Get all active salespeople."""
    stmt = select(Salesperson).where(Salesperson.is_active == True).order_by(Salesperson.name)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_all_salespeople(db: AsyncSession) -> list[Salesperson]:
    """Get all salespeople (active and inactive)."""
    stmt = select(Salesperson).order_by(Salesperson.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_salesperson_by_id(db: AsyncSession, sp_id: int) -> Salesperson | None:
    result = await db.execute(select(Salesperson).where(Salesperson.id == sp_id))
    return result.scalar_one_or_none()


async def create_salesperson(
    db: AsyncSession,
    name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    user_id: Optional[int] = None,
    ref_code: Optional[str] = None,
    notes: Optional[str] = None,
    notification_webhook_url: Optional[str] = None,
) -> Salesperson:
    """Create a new salesperson."""
    sp = Salesperson(
        name=name,
        phone=phone,
        email=email,
        user_id=user_id,
        ref_code=ref_code,
        notes=notes,
        notification_webhook_url=notification_webhook_url,
    )
    db.add(sp)
    await db.flush()
    return sp


async def update_salesperson(db: AsyncSession, sp_id: int, **kwargs) -> Salesperson | None:
    """Update salesperson fields."""
    sp = await get_salesperson_by_id(db, sp_id)
    if not sp:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(sp, key):
            setattr(sp, key, value)
    await db.flush()
    return sp


async def ensure_salesperson_for_user(db: AsyncSession, user: User) -> Salesperson | None:
    """
    When a user gets role=salesperson, ensure a Salesperson record exists and is linked.
    If the user already has a linked Salesperson, reactivate it.
    If not, create a new one with the user's details.
    Returns the Salesperson or None if user role is not salesperson.
    """
    is_sales_role = user.role_name == "salesperson"

    # Check if user already has a linked salesperson
    stmt = select(Salesperson).where(Salesperson.user_id == user.id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        if is_sales_role:
            # Reactivate and sync name/email
            existing.is_active = True
            existing.name = user.full_name
            if user.email and not existing.email:
                existing.email = user.email
            await db.flush()
            return existing
        else:
            # User lost salesperson role — deactivate (don't delete, has leads)
            existing.is_active = False
            await db.flush()
            return existing

    if not is_sales_role:
        return None

    # Create new salesperson linked to user
    sp = Salesperson(
        user_id=user.id,
        name=user.full_name,
        email=user.email,
        is_active=True,
    )
    db.add(sp)
    await db.flush()
    return sp


async def get_salesperson_stats(db: AsyncSession, sp_id: int) -> dict:
    """Get lead statistics for a salesperson."""
    total_stmt = select(func.count(Lead.id)).where(Lead.salesperson_id == sp_id)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    open_statuses = ["ליד חדש", "ליד בתהליך", "חיוג ראשון", "במעקב", "מתעניין"]
    open_stmt = select(func.count(Lead.id)).where(
        Lead.salesperson_id == sp_id,
        Lead.status.in_(open_statuses),
    )
    open_result = await db.execute(open_stmt)
    open_leads = open_result.scalar() or 0

    converted_stmt = select(func.count(Lead.id)).where(
        Lead.salesperson_id == sp_id,
        Lead.status.in_(["converted", "תלמיד פעיל", "ליד סגור - לקוח"]),
    )
    converted_result = await db.execute(converted_stmt)
    converted = converted_result.scalar() or 0

    return {
        "total_leads": total,
        "open_leads": open_leads,
        "converted_leads": converted,
    }


async def create_task(
    db: AsyncSession,
    salesperson_id: int,
    title: str,
    lead_id: int | None = None,
    description: str | None = None,
    due_date: datetime | None = None,
    priority: int = 0,
) -> SalesTask:
    """Create a new task for a salesperson."""
    task = SalesTask(
        salesperson_id=salesperson_id,
        lead_id=lead_id,
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
    )
    db.add(task)
    await db.flush()
    return task


async def complete_task(db: AsyncSession, task_id: int) -> SalesTask | None:
    """Mark a task as completed."""
    stmt = select(SalesTask).where(SalesTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        return None

    task.status = "הושלם"
    task.completed_at = func.now()
    await db.flush()
    return task


async def get_salesperson_dashboard(db: AsyncSession, salesperson_id: int) -> dict:
    """Get dashboard data for a salesperson."""
    # Lead counts
    leads_stmt = select(func.count()).select_from(Lead).where(Lead.salesperson_id == salesperson_id)
    total_result = await db.execute(leads_stmt)
    total_leads = total_result.scalar() or 0

    new_leads_stmt = leads_stmt.where(Lead.status == "ליד חדש")
    new_result = await db.execute(new_leads_stmt)
    new_leads = new_result.scalar() or 0

    # Open tasks
    tasks_stmt = (
        select(SalesTask)
        .where(SalesTask.salesperson_id == salesperson_id, SalesTask.status != "הושלם")
        .order_by(SalesTask.due_date.asc().nullslast())
        .limit(20)
    )
    tasks_result = await db.execute(tasks_stmt)
    open_tasks = list(tasks_result.scalars().all())

    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "open_tasks": open_tasks,
    }
