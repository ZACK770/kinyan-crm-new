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
    from db.models import Lead
    stmt = select(SalesTask).options(
        selectinload(SalesTask.reports),
        selectinload(SalesTask.lead)
    )

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

    # Default sort: due_date ascending (tasks due soonest first), then created_at descending
    stmt = stmt.order_by(SalesTask.due_date.asc().nulls_last(), SalesTask.created_at.desc()).offset(offset).limit(limit)
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
    
    print(f"[create_task] Task created with ID: {task.id}, title: {task.title}, lead_id: {task.lead_id}")
    
    # Create HistoryEntry if linked to a lead
    if task.lead_id:
        print(f"[create_task] Creating HistoryEntry for lead_id: {task.lead_id}")
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
        print(f"[create_task] HistoryEntry created with ID: {history.id}")
    else:
        print(f"[create_task] No lead_id, skipping HistoryEntry creation")
    
    print(f"[create_task] Task creation completed successfully")
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
# Bulk Operations
# ============================================================
async def bulk_update_tasks(db: AsyncSession, task_ids: list[int], field: str, value: any) -> int:
    """
    Update a specific field for multiple tasks.
    """
    if not task_ids:
        return 0
    
    allowed = {
        "status": ALLOWED_TASK_STATUSES,
        "priority": None,  # numeric, no validation needed
        "salesperson_id": None,
        "assigned_to_user_id": None,
    }
    
    if field not in allowed:
        raise ValueError(f"Field '{field}' is not allowed for bulk update")
    
    if allowed[field] is not None and value not in allowed[field]:
        raise ValueError(f"Value '{value}' is not allowed for field '{field}'")
    
    from sqlalchemy import update as sa_update
    stmt = sa_update(SalesTask).where(SalesTask.id.in_(task_ids)).values({field: value})
    result = await db.execute(stmt)
    return result.rowcount


async def bulk_delete_tasks(db: AsyncSession, task_ids: list[int]) -> dict:
    """
    Delete multiple tasks by their IDs.
    """
    from sqlalchemy import delete as sa_delete
    
    if not task_ids:
        return {"success": True, "deleted_count": 0}
    
    # Delete task reports first
    await db.execute(sa_delete(TaskReport).where(TaskReport.task_id.in_(task_ids)))
    
    # Delete tasks
    stmt = sa_delete(SalesTask).where(SalesTask.id.in_(task_ids))
    result = await db.execute(stmt)
    deleted_count = result.rowcount
    
    return {"success": True, "deleted_count": deleted_count}


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


# ============================================================
# Metrics — aggregated task statistics for dashboard
# ============================================================
async def get_task_metrics(db: AsyncSession) -> dict:
    """Get aggregated task metrics for the dashboard."""
    print("[DEBUG] get_task_metrics service started")
    from db.models import Salesperson, User
    from sqlalchemy import case, literal_column

    now = datetime.now(timezone.utc)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    print("[DEBUG] Getting tasks by status")
    # Total tasks by status
    status_stmt = (
        select(
            SalesTask.status,
            func.count(SalesTask.id).label('count')
        )
        .group_by(SalesTask.status)
    )
    status_result = await db.execute(status_stmt)
    by_status = {row.status: row.count for row in status_result}
    print(f"[DEBUG] by_status: {by_status}")

    # Tasks by user (assigned_to_user_id) - only open tasks
    user_stmt = (
        select(
            SalesTask.assigned_to_user_id,
            func.count(SalesTask.id).label('count')
        )
        .where(
            SalesTask.assigned_to_user_id.isnot(None),
            SalesTask.status.in_(["חדש", "בטיפול"])
        )
        .group_by(SalesTask.assigned_to_user_id)
    )
    user_result = await db.execute(user_stmt)
    by_user = {row.assigned_to_user_id: row.count for row in user_result}

    # Get user names for the IDs
    user_ids = list(by_user.keys()) if by_user else []
    user_names = {}
    if user_ids:
        users_stmt = select(User.id, User.email).where(User.id.in_(user_ids))
        users_result = await db.execute(users_stmt)
        user_names = {row.id: row.email for row in users_result}

    by_user_with_names = [
        {"user_id": uid, "name": user_names.get(uid, f"User {uid}"), "count": count}
        for uid, count in by_user.items()
    ]
    by_user_with_names.sort(key=lambda x: x["count"], reverse=True)

    # Tasks by salesperson - only open tasks
    sp_stmt = (
        select(
            SalesTask.salesperson_id,
            func.count(SalesTask.id).label('count')
        )
        .where(
            SalesTask.salesperson_id.isnot(None),
            SalesTask.status.in_(["חדש", "בטיפול"])
        )
        .group_by(SalesTask.salesperson_id)
    )
    sp_result = await db.execute(sp_stmt)
    by_salesperson = {row.salesperson_id: row.count for row in sp_result}

    # Get salesperson names for the IDs
    sp_ids = list(by_salesperson.keys()) if by_salesperson else []
    sp_names = {}
    if sp_ids:
        sps_stmt = select(Salesperson.id, Salesperson.name).where(Salesperson.id.in_(sp_ids))
        sps_result = await db.execute(sps_stmt)
        sp_names = {row.id: row.name for row in sps_result}

    by_salesperson_with_names = [
        {"salesperson_id": sid, "name": sp_names.get(sid, f"SP {sid}"), "count": count}
        for sid, count in by_salesperson.items()
    ]
    by_salesperson_with_names.sort(key=lambda x: x["count"], reverse=True)

    # Tasks by priority - only open tasks
    priority_stmt = (
        select(
            SalesTask.priority,
            func.count(SalesTask.id).label('count')
        )
        .where(SalesTask.status.in_(["חדש", "בטיפול"]))
        .group_by(SalesTask.priority)
    )
    priority_result = await db.execute(priority_stmt)
    by_priority = {row.priority: row.count for row in priority_result}

    # Tasks by type - only open tasks
    type_stmt = (
        select(
            SalesTask.task_type,
            func.count(SalesTask.id).label('count')
        )
        .where(SalesTask.status.in_(["חדש", "בטיפול"]))
        .group_by(SalesTask.task_type)
    )
    type_result = await db.execute(type_stmt)
    by_type = {row.task_type: row.count for row in type_result}

    # Overdue tasks
    overdue_count = await count_tasks(db, overdue=True)

    # Tasks created today
    created_today_stmt = select(func.count()).where(SalesTask.created_at >= today_start)
    created_today_result = await db.execute(created_today_stmt)
    created_today = created_today_result.scalar() or 0

    # Tasks completed today
    completed_today_stmt = select(func.count()).where(
        SalesTask.completed_at >= today_start,
        SalesTask.status == "הושלם"
    )
    completed_today_result = await db.execute(completed_today_stmt)
    completed_today = completed_today_result.scalar() or 0

    # Total open tasks
    total_open = by_status.get("חדש", 0) + by_status.get("בטיפול", 0)
    total_completed = by_status.get("הושלם", 0)
    total_cancelled = by_status.get("בוטל", 0)
    total_all = sum(by_status.values())

    return {
        "by_status": by_status,
        "by_user": by_user_with_names,
        "by_salesperson": by_salesperson_with_names,
        "by_priority": by_priority,
        "by_type": by_type,
        "overdue_count": overdue_count,
        "created_today": created_today,
        "completed_today": completed_today,
        "summary": {
            "total_all": total_all,
            "total_open": total_open,
            "total_completed": total_completed,
            "total_cancelled": total_cancelled,
            "completion_rate": round(total_completed / total_all * 100, 1) if total_all > 0 else 0,
        },
    }
