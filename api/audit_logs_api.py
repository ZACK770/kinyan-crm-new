"""
API endpoints for audit logs (system activity logging).
Allows viewing all system actions, user activities, and entity changes.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from db import get_db
from db.models import User
from api.dependencies import get_current_user, require_permission
from services.audit_logs import get_audit_logs, get_entity_logs, get_user_activity


router = APIRouter()


# ============================================================
# Pydantic Schemas
# ============================================================

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_method: Optional[str]
    request_path: Optional[str]
    changes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogsListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


# ============================================================
# Routes
# ============================================================

@router.get("/", response_model=AuditLogsListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    user_id: Optional[int] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    days: Optional[int] = Query(None, ge=1, le=365),
    current_user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """
    List all audit logs with optional filtering.
    Requires manager or admin permission.
    
    Query params:
    - page: Page number (1-indexed)
    - page_size: Number of records per page
    - user_id: Filter by specific user
    - entity_type: Filter by entity type (leads, students, etc.)
    - action: Filter by action type (create, update, delete, view, login)
    - days: Only show logs from the last N days
    """
    skip = (page - 1) * page_size
    
    logs, total = await get_audit_logs(
        db=db,
        skip=skip,
        limit=page_size,
        user_id=user_id,
        entity_type=entity_type,
        action=action,
        days=days,
    )
    
    return AuditLogsListResponse(
        logs=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
async def get_entity_audit_logs(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_permission("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get audit logs for a specific entity.
    Shows all changes made to a particular record.
    
    Example: GET /api/audit-logs/entity/students/123
    """
    logs = await get_entity_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/user/{user_id}", response_model=List[AuditLogResponse])
async def get_user_audit_logs(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent activity for a specific user.
    Requires manager or admin permission.
    """
    logs = await get_user_activity(
        db=db,
        user_id=user_id,
        days=days,
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/my-activity", response_model=List[AuditLogResponse])
async def get_my_activity(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get your own recent activity.
    Any authenticated user can view their own logs.
    """
    logs = await get_user_activity(
        db=db,
        user_id=current_user.id,
        days=days,
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]
