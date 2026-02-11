"""
Sales management service.
Salespeople dashboard, tasks, lead assignment.
"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Salesperson, SalesTask, Lead


async def get_active_salespeople(db: AsyncSession) -> list[Salesperson]:
    """Get all active salespeople."""
    stmt = select(Salesperson).where(Salesperson.is_active == True).order_by(Salesperson.name)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


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
