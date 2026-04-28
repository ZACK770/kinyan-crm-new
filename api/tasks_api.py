"""
Tasks API — CRUD endpoints for SalesTask + TaskReport.
Supports tasks for salespeople AND regular users.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, get_async_session
from .dependencies import require_entity_access, require_permission, get_current_user
from services import audit_logs
import services.tasks as task_svc
import services.tasks_email_service as task_email_svc
from services.tasks_scheduler import schedule_task_reminder, cancel_task_reminder

router = APIRouter()


# ── Schemas ──────────────────────────────────────────
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "חדש"
    priority: int = Field(default=0, ge=0, le=3)
    task_type: str = "general"
    salesperson_id: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    lead_id: Optional[int] = None
    student_id: Optional[int] = None
    send_reminder: bool = True  # Send reminder email at due date


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0, le=3)
    task_type: Optional[str] = None
    salesperson_id: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    lead_id: Optional[int] = None
    student_id: Optional[int] = None
    send_reminder: Optional[bool] = None


class ReportCreate(BaseModel):
    description: Optional[str] = None
    duration: Optional[str] = None


def _task_to_dict(t) -> dict:
    # Don't access t.reports to avoid lazy loading in async context
    # For newly created tasks, reports will be empty anyway
    print(f"[_task_to_dict] Converting task #{t.id} to dict")
    reports_data = []  # Don't lazy load in async context
    print(f"[_task_to_dict] Task #{t.id} converted successfully")

    # Extract lead details if available
    lead_data = None
    if hasattr(t, 'lead') and t.lead:
        lead_data = {
            "id": t.lead.id,
            "full_name": t.lead.full_name,
            "phone": t.lead.phone,
            "email": t.lead.email,
        }

    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "due_date": str(t.due_date) if t.due_date else None,
        "status": t.status,
        "priority": t.priority,
        "task_type": t.task_type,
        "salesperson_id": t.salesperson_id,
        "assigned_to_user_id": t.assigned_to_user_id,
        "lead_id": t.lead_id,
        "student_id": t.student_id,
        "auto_created": t.auto_created,
        "parent_lead_conversion": t.parent_lead_conversion,
        "send_reminder": t.send_reminder,
        "created_at": str(t.created_at) if t.created_at else None,
        "completed_at": str(t.completed_at) if t.completed_at else None,
        "reports": reports_data,
        "lead": lead_data,
    }


# ── Debug endpoint (for remote debugging) ────────────────
@router.get("/debug/info")
async def debug_info(
    user=Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Debug endpoint for remote troubleshooting - admin only."""
    from db.models import SalesTask
    from sqlalchemy import func

    # Get task count
    count_result = await db.execute(select(func.count(SalesTask.id)))
    task_count = count_result.scalar() or 0

    return {
        "status": "ok",
        "task_count": task_count,
        "user": {
            "id": user.id,
            "email": user.email,
            "permission_level": user.permission_level,
            "role_name": user.role_name,
        },
        "permissions": {
            "tasks": {
                "view": 10,
                "create": 20,
                "edit": 20,
                "delete": 30,
            }
        }
    }


# ── Notifications (for bell icon) — MUST be before /{task_id} ──
@router.get("/notifications/summary")
async def task_notifications(
    user=Depends(require_entity_access("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    from db.models import Salesperson
    user_id = user.id
    if not user_id:
        return {"overdue_count": 0, "new_today_count": 0, "total_open": 0}
    # Look up salesperson linked to this user
    sp_result = await db.execute(
        select(Salesperson.id).where(Salesperson.user_id == user_id)
    )
    salesperson_id = sp_result.scalar_one_or_none()
    return await task_svc.get_task_notifications(db, user_id, salesperson_id)


# ── List ─────────────────────────────────────────────
@router.get("/")
async def list_tasks(
    status: str | None = Query(None),
    salesperson_id: int | None = Query(None),
    assigned_to_user_id: int | None = Query(None),
    lead_id: int | None = Query(None),
    student_id: int | None = Query(None),
    task_type: str | None = Query(None),
    limit: int = Query(200, le=1000),
    offset: int = Query(0),
    user=Depends(require_entity_access("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await task_svc.list_tasks(
        db,
        status=status,
        salesperson_id=salesperson_id,
        assigned_to_user_id=assigned_to_user_id,
        lead_id=lead_id,
        student_id=student_id,
        task_type=task_type,
        limit=limit,
        offset=offset,
    )
    return [_task_to_dict(t) for t in items]


# ── Get ──────────────────────────────────────────────
@router.get("/{task_id}")
async def get_task(
    task_id: int,
    user=Depends(require_entity_access("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    task = await task_svc.get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return _task_to_dict(task)


# ── Create ───────────────────────────────────────────
@router.post("/")
async def create_task(
    data: TaskCreate,
    request: Request,
    user=Depends(require_entity_access("tasks", "edit")),
    db: AsyncSession = Depends(get_db),
):
    print(f"[create_task API] Starting task creation")
    print(f"[create_task API] User: {user.email if user else 'None'}")
    
    # Convert data to dict
    task_data = data.model_dump()
    print(f"[create_task API] Task data received: {task_data}")
    
    # Create task
    print(f"[create_task API] Calling task_svc.create_task")
    try:
        task = await task_svc.create_task(db, **task_data)
        print(f"[create_task API] Task created with ID: {task.id}, title: {task.title}, lead_id: {task.lead_id}")
    except ValueError as e:
        print(f"[create_task API] ValueError: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"[create_task API] Unexpected error creating task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))
    
    # Schedule reminder if due_date and send_reminder
    if task.due_date and task.send_reminder:
        print(f"[create_task API] Scheduling reminder for task {task.id} at {task.due_date}")
        try:
            await schedule_task_reminder(task.id, task.due_date)
            print(f"[create_task API] Reminder scheduled successfully")
        except Exception as e:
            print(f"[create_task API] Error scheduling reminder: {e}")
    else:
        print(f"[create_task API] Not scheduling reminder - due_date: {task.due_date}, send_reminder: {task.send_reminder}")
    
    # Log task creation
    print(f"[create_task API] Logging audit log")
    try:
        await audit_logs.log_action(
            db,
            action="create_task",
            entity_id=task.id,
            entity_type="task",
            details={
                "title": task.title,
                "lead_id": task.lead_id,
                "salesperson_id": task.salesperson_id,
                "due_date": str(task.due_date) if task.due_date else None,
                "send_reminder": task.send_reminder,
            },
        )
        print(f"[create_task API] Audit log created")
    except Exception as e:
        print(f"[create_task API] Error creating audit log: {e}")
    
    await db.commit()
    print(f"[create_task API] Transaction committed")
    
    print(f"[create_task API] Converting task to dict for response...")
    result = _task_to_dict(task)
    print(f"[create_task API] Task creation completed successfully")
    return result


# ── Update ───────────────────────────────────────────
@router.patch("/{task_id}")
async def update_task(
    task_id: int,
    data: TaskUpdate,
    request: Request,
    user=Depends(require_entity_access("tasks", "edit")),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await task_svc.update_task(db, task_id, **data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not task:
        raise HTTPException(404, "Task not found")
    await db.commit()
    
    changes = data.model_dump(exclude_unset=True)
    
    # Handle reminder scheduling based on changes
    if 'due_date' in changes or 'send_reminder' in changes:
        if task.due_date and task.send_reminder:
            # Schedule or reschedule reminder
            try:
                await schedule_task_reminder(task.id, task.due_date)
                print(f"[update_task] Scheduled reminder for task #{task_id} at {task.due_date}")
            except Exception as e:
                print(f"[update_task] Failed to schedule reminder: {e}")
        elif not task.due_date or not task.send_reminder:
            # Cancel reminder if due_date was removed or send_reminder was set to False
            try:
                await cancel_task_reminder(task.id)
                print(f"[update_task] Cancelled reminder for task #{task_id}")
            except Exception as e:
                print(f"[update_task] Failed to cancel reminder: {e}")
    
    await audit_logs.log_update(
        db=db, user=user, entity_type="tasks", entity_id=task_id,
        description=f"עודכנה משימה: {task.title}",
        changes=changes,
        request=request,
    )
    return _task_to_dict(task)


# ── Delete ───────────────────────────────────────────
@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    request: Request,
    user = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    deleted = await task_svc.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(404, "Task not found")
    
    # Cancel scheduled reminder if exists
    try:
        await cancel_task_reminder(task_id)
        print(f"[delete_task] Cancelled reminder for deleted task #{task_id}")
    except Exception as e:
        print(f"[delete_task] Failed to cancel reminder: {e}")
    
    await db.commit()
    await audit_logs.log_delete(
        db=db, user=user, entity_type="tasks", entity_id=task_id,
        description=f"נמחקה משימה #{task_id}",
        request=request,
    )
    return {"deleted": True}


# ── Add Report ───────────────────────────────────────
@router.post("/{task_id}/reports")
async def add_report(
    task_id: int,
    data: ReportCreate,
    request: Request,
    user=Depends(require_entity_access("tasks", "edit")),
    db: AsyncSession = Depends(get_db),
):
    task = await task_svc.get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    report = await task_svc.add_report(db, task_id, **data.model_dump())
    await db.commit()
    return {
        "id": report.id,
        "description": report.description,
        "duration": report.duration,
        "created_at": str(report.created_at) if report.created_at else None,
    }


# ── Send Reminder Email ─────────────────────────────────
@router.post("/{task_id}/send-reminder")
async def send_task_reminder(
    task_id: int,
    user=Depends(require_entity_access("tasks", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Send a reminder email for a specific task to the assigned salesperson."""
    task = await task_svc.get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    success = await task_email_svc.send_task_reminder_email(db, task_id)
    
    if success:
        return {"success": True, "message": "Reminder email sent successfully"}
    else:
        raise HTTPException(500, "Failed to send reminder email")


# ── Daily Summary Email ─────────────────────────────────
@router.post("/daily-summary/{salesperson_id}")
async def send_daily_summary(
    salesperson_id: int,
    user=Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Send a daily summary email to a specific salesperson."""
    success = await task_email_svc.send_daily_summary_email(db, salesperson_id)
    
    if success:
        return {"success": True, "message": "Daily summary email sent successfully"}
    else:
        raise HTTPException(500, "Failed to send daily summary email")


@router.post("/daily-summary/all")
async def send_daily_summary_all(
    user=Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Send daily summary emails to all active salespeople."""
    result = await task_email_svc.send_daily_summary_to_all_salespeople(db)
    return result


# ── Popup Notifications ───────────────────────────────────
@router.get("/popup-notifications")
async def get_popup_notifications(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get open tasks for the current user (salesperson) to show as popup notification.
    Returns tasks with status 'חדש' or 'בטיפול' assigned to this user.
    """
    from db.models import Salesperson
    
    user_id = user.id if user else None
    if not user_id:
        return {"tasks": [], "count": 0}
    
    # Find salesperson linked to this user
    sp_result = await db.execute(
        select(Salesperson.id).where(Salesperson.user_id == user_id)
    )
    salesperson_id = sp_result.scalar_one_or_none()
    
    if not salesperson_id:
        return {"tasks": [], "count": 0}
    
    # Get open tasks for this salesperson
    items = await task_svc.list_tasks(
        db,
        salesperson_id=salesperson_id,
        status=None,  # Will filter in query
        limit=50,
    )
    
    # Filter for open tasks only
    open_tasks = [t for t in items if t.status in ["חדש", "בטיפול"]]
    
    return {
        "tasks": [_task_to_dict(t) for t in open_tasks],
        "count": len(open_tasks),
    }


@router.get("/due-reminders")
async def get_due_reminders(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tasks that are due now and have send_reminder=True.
    Used for popup notifications in the frontend.
    """
    from db.models import Salesperson
    from datetime import datetime, timezone, timedelta

    user_id = user.id if user else None
    if not user_id:
        return []

    # Find salesperson linked to this user
    sp_result = await db.execute(
        select(Salesperson.id).where(Salesperson.user_id == user_id)
    )
    salesperson_id = sp_result.scalar_one_or_none()

    if not salesperson_id:
        return []

    # Get tasks for this salesperson with send_reminder=True and due_date <= now
    items = await task_svc.list_tasks(
        db,
        salesperson_id=salesperson_id,
        limit=50,
    )

    # Filter for due tasks with reminders
    now = datetime.now(timezone.utc)
    due_tasks = [
        t for t in items
        if t.send_reminder
        and t.due_date
        and t.due_date <= now
        and t.status not in ["הושלם", "בוטל"]
    ]

    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": t.due_date.isoformat() if t.due_date else None,
        }
        for t in due_tasks
    ]


# ── Metrics Dashboard ───────────────────────────────────────
@router.get("/metrics")
async def get_task_metrics(
    user=Depends(require_entity_access("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated task metrics for the dashboard.
    Returns statistics by status, user, salesperson, priority, type, and more.
    """
    return await task_svc.get_task_metrics(db)


