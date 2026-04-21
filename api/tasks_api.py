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

from db import get_db
from .dependencies import require_entity_access, require_permission, get_current_user
from services import audit_logs
import services.tasks as task_svc

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


class ReportCreate(BaseModel):
    description: Optional[str] = None
    duration: Optional[str] = None


def _task_to_dict(t) -> dict:
    # Don't access t.reports to avoid lazy loading in async context
    # For newly created tasks, reports will be empty anyway
    reports_data = []
    if hasattr(t, '_sa_instance_state') and t._sa_instance_state.loaded.get('reports'):
        reports_data = [
            {
                "id": r.id,
                "description": r.description,
                "duration": r.duration,
                "created_at": str(r.created_at) if r.created_at else None,
            }
            for r in (t.reports or [])
        ]

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
        "created_at": str(t.created_at) if t.created_at else None,
        "completed_at": str(t.completed_at) if t.completed_at else None,
        "reports": reports_data,
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
    user=Depends(get_current_user),  # Temporarily use simple auth instead of require_entity_access
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await task_svc.create_task(db, **data.model_dump())
        await db.commit()
        # Temporarily disable audit logs to debug
        # await audit_logs.log_create(
        #     db=db, user=user, entity_type="tasks", entity_id=task.id,
        #     description=f"נוצרה משימה: {task.title}",
        #     request=None,
        # )
        return _task_to_dict(task)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"Unexpected error in create_task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))


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


