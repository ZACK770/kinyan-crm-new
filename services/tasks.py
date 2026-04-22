"""
Tasks service — CRUD for SalesTask + TaskReport.
Supports tasks for salespeople AND regular users (class managers, etc.)
"""
from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import SalesTask, TaskReport, HistoryEntry

ALLOWED_TASK_STATUSES = {"חדש", "בטיפול", "הושלם", "בוטל"}
ALLOWED_TASK_TYPES = {"sales", "class_management", "shipping", "general"}


# ============================================================
# List / Get
# ============================================================
async def list_tasks(
    db: AsyncSession,
    *,
    status: str | None = None,
    salesperson_id: int | None = None,
    assigned_to_user_id: int | None = None,
    lead_id: int | None = None,
    student_id: int | None = None,
    task_type: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[SalesTask]:
    stmt = select(SalesTask).options(selectinload(SalesTask.reports))

    if status:
        stmt = stmt.where(SalesTask.status == status)
    if salesperson_id is not None:
        stmt = stmt.where(SalesTask.salesperson_id == salesperson_id)
    if assigned_to_user_id is not None:
        stmt = stmt.where(SalesTask.assigned_to_user_id == assigned_to_user_id)
    if lead_id is not None:
        stmt = stmt.where(SalesTask.lead_id == lead_id)
    if student_id is not None:
        stmt = stmt.where(SalesTask.student_id == student_id)
    if task_type:
        stmt = stmt.where(SalesTask.task_type == task_type)

    stmt = stmt.order_by(SalesTask.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: int) -> SalesTask | None:
    stmt = (
        select(SalesTask)
        .options(selectinload(SalesTask.reports))
        .where(SalesTask.id == task_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def count_tasks(
    db: AsyncSession,
    *,
    status: str | None = None,
    assigned_to_user_id: int | None = None,
    salesperson_id: int | None = None,
    overdue: bool = False,
) -> int:
    stmt = select(func.count(SalesTask.id))
    if status:
        stmt = stmt.where(SalesTask.status == status)
    if assigned_to_user_id is not None:
        stmt = stmt.where(SalesTask.assigned_to_user_id == assigned_to_user_id)
    if salesperson_id is not None:
        stmt = stmt.where(SalesTask.salesperson_id == salesperson_id)
    if overdue:
        now = datetime.now(timezone.utc)
        stmt = stmt.where(
            SalesTask.due_date < now,
            SalesTask.status.in_(["חדש", "בטיפול"]),
        )
    result = await db.execute(stmt)
    return result.scalar() or 0


# ============================================================
# Create
# ============================================================
async def create_task(db: AsyncSession, **kwargs) -> SalesTask:
    status = kwargs.get("status", "חדש")
    if status not in ALLOWED_TASK_STATUSES:
        raise ValueError(f"סטטוס משימה לא חוקי: {status}")

    task_type = kwargs.get("task_type", "general")
    if task_type not in ALLOWED_TASK_TYPES:
        raise ValueError(f"סוג משימה לא חוקי: {task_type}")

    task = SalesTask(
        title=kwargs["title"],
        description=kwargs.get("description"),
        due_date=kwargs.get("due_date"),
        status=status,
        priority=kwargs.get("priority", 0),
        task_type=task_type,
        salesperson_id=kwargs.get("salesperson_id"),
        assigned_to_user_id=kwargs.get("assigned_to_user_id"),
        lead_id=kwargs.get("lead_id"),
        student_id=kwargs.get("student_id"),
        auto_created=kwargs.get("auto_created", False),
        parent_lead_conversion=kwargs.get("parent_lead_conversion", False),
        send_reminder=kwargs.get("send_reminder", True),
    )
    db.add(task)
    await db.flush()

    # Create HistoryEntry if task is linked to a lead
    if task.lead_id:
        history = HistoryEntry(
            lead_id=task.lead_id,
            action_type="משימה נוצרה",
            description=f"נוצרה משימה: {task.title}",
            extra_data={
                "task_id": task.id,
                "task_title": task.title,
                "task_status": task.status,
                "task_due_date": str(task.due_date) if task.due_date else None,
                "task_priority": task.priority,
                "send_reminder": task.send_reminder,
            }
        )
        db.add(history)
        await db.flush()

    return task


# ============================================================
# Update
# ============================================================
async def update_task(db: AsyncSession, task_id: int, **kwargs) -> SalesTask | None:
    task = await get_task(db, task_id)
    if not task:
        return None

    # Track status change for history entry
    old_status = task.status

    # Validate status if provided
    if "status" in kwargs and kwargs["status"] is not None:
        if kwargs["status"] not in ALLOWED_TASK_STATUSES:
            raise ValueError(f"סטטוס משימה לא חוקי: {kwargs['status']}")

    # Update fields
    for key, value in kwargs.items():
        if hasattr(task, key) and value is not None:
            setattr(task, key, value)
    
    await db.flush()
    
    # Create HistoryEntry for status change if linked to a lead
    if task.lead_id and old_status != task.status:
        history = HistoryEntry(
            lead_id=task.lead_id,
            action_type="סטטוס משימה השתנה",
            description=f"סטטוס משימה שונה מ-{old_status} ל-{task.status}",
            extra_data={
                "task_id": task.id,
                "task_title": task.title,
                "old_status": old_status,
                "new_status": task.status,
            }
        )
        db.add(history)
        await db.flush()
    
    return task


# ============================================================
# Delete
# ============================================================
async def delete_task(db: AsyncSession, task_id: int) -> bool:
    from sqlalchemy import delete as sa_delete
    task = await get_task(db, task_id)
    if not task:
        return False
    await db.execute(sa_delete(TaskReport).where(TaskReport.task_id == task_id))
    await db.execute(sa_delete(SalesTask).where(SalesTask.id == task_id))
    await db.flush()
    return True


# ============================================================
# Task Reports
# ============================================================
async def add_report(db: AsyncSession, task_id: int, **kwargs) -> TaskReport:
    report = TaskReport(
        task_id=task_id,
        description=kwargs.get("description"),
        duration=kwargs.get("duration"),
    )
    db.add(report)
    await db.flush()
    return report


# ============================================================
# Notifications — overdue/new tasks for a user
# ============================================================
async def get_task_notifications(
    db: AsyncSession,
    user_id: int,
    salesperson_id: int | None = None,
) -> dict:
    """Get task notification counts for the bell icon."""
    now = datetime.now(timezone.utc)

    # Build filter: tasks assigned to this user OR their salesperson
    conditions = [SalesTask.assigned_to_user_id == user_id]
    if salesperson_id:
        conditions.append(SalesTask.salesperson_id == salesperson_id)

    base = select(SalesTask).where(
        or_(*conditions),
        SalesTask.status.in_(["חדש", "בטיפול"]),
    )

    # Overdue tasks
    overdue_stmt = select(func.count()).select_from(
        base.where(SalesTask.due_date < now).subquery()
    )
    overdue_result = await db.execute(overdue_stmt)
    overdue_count = overdue_result.scalar() or 0

    # New tasks (created in last 24h)
    day_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    new_stmt = select(func.count()).select_from(
        base.where(SalesTask.created_at >= day_ago).subquery()
    )
    new_result = await db.execute(new_stmt)
    new_count = new_result.scalar() or 0

    return {
        "overdue_count": overdue_count,
        "new_today_count": new_count,
        "total_open": overdue_count + new_count,
    }
