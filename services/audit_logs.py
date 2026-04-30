"""
Service layer for audit logging.
Provides helper functions to log all user and system actions.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import Request

from db.models import AuditLog, User
import json


async def create_audit_log(
    db: AsyncSession,
    action: str,
    user: Optional[User] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    description: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """
    Create a new audit log entry.
    
    Args:
        db: Database session
        action: Action type (create/update/delete/view/login/etc)
        user: The user who performed the action (None for system actions)
        entity_type: Type of entity affected (leads/students/courses/etc)
        entity_id: ID of the affected entity
        description: Human-readable description of the action
        changes: Dictionary of changes (before/after values)
        request: FastAPI Request object to extract IP, user-agent, etc.
    
    Returns:
        The created AuditLog instance
    """
    log_data = {
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "description": description,
    }

    if user:
        # Only set user_id if it's a real user (not dev fake user with id=0)
        if user.id and user.id > 0:
            log_data["user_id"] = user.id
        log_data["user_name"] = user.full_name

    if changes:
        log_data["changes"] = json.dumps(changes, ensure_ascii=False, default=str)

    if request:
        log_data["ip_address"] = request.client.host if request.client else None
        log_data["user_agent"] = request.headers.get("user-agent")
        log_data["request_method"] = request.method
        log_data["request_path"] = str(request.url.path)

    audit_log = AuditLog(**log_data)
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    
    return audit_log


async def get_audit_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    days: Optional[int] = None,
) -> tuple[list[AuditLog], int]:
    """
    Retrieve audit logs with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        user_id: Filter by specific user
        entity_type: Filter by entity type
        action: Filter by action type
        days: Only show logs from the last N days
    
    Returns:
        Tuple of (logs list, total count)
    """
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_query = count_query.where(AuditLog.entity_type == entity_type)

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)

    if days:
        since = datetime.utcnow() - timedelta(days=days)
        query = query.where(AuditLog.created_at >= since)
        count_query = count_query.where(AuditLog.created_at >= since)

    # Order by most recent first
    query = query.order_by(desc(AuditLog.created_at))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return list(logs), total


async def get_entity_logs(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    limit: int = 50,
) -> list[AuditLog]:
    """
    Get audit logs for a specific entity (e.g., all changes to a specific student).
    
    Args:
        db: Database session
        entity_type: Type of entity (leads/students/etc)
        entity_id: ID of the entity
        limit: Maximum number of records
    
    Returns:
        List of audit logs
    """
    query = (
        select(AuditLog)
        .where(AuditLog.entity_type == entity_type)
        .where(AuditLog.entity_id == entity_id)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_activity(
    db: AsyncSession,
    user_id: int,
    days: int = 30,
) -> list[AuditLog]:
    """
    Get recent activity for a specific user.
    
    Args:
        db: Database session
        user_id: User ID
        days: Number of days to look back
    
    Returns:
        List of audit logs
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .where(AuditLog.created_at >= since)
        .order_by(desc(AuditLog.created_at))
        .limit(100)
    )
    
    result = await db.execute(query)
    return list(result.scalars().all())


# Helper function to easily log CRUD operations
async def log_create(db: AsyncSession, user: User, entity_type: str, entity_id: int, description: str, request: Optional[Request] = None):
    """Log a CREATE action"""
    return await create_audit_log(
        db=db,
        action="create",
        user=user,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        request=request,
    )


async def log_update(db: AsyncSession, user: User, entity_type: str, entity_id: int, description: str, changes: Optional[Dict] = None, request: Optional[Request] = None):
    """Log an UPDATE action"""
    return await create_audit_log(
        db=db,
        action="update",
        user=user,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        changes=changes,
        request=request,
    )


async def log_delete(db: AsyncSession, user: User, entity_type: str, entity_id: int, description: str, request: Optional[Request] = None):
    """Log a DELETE action"""
    return await create_audit_log(
        db=db,
        action="delete",
        user=user,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        request=request,
    )


async def log_view(db: AsyncSession, user: User, entity_type: str, description: str, request: Optional[Request] = None):
    """Log a VIEW action"""
    return await create_audit_log(
        db=db,
        action="view",
        user=user,
        entity_type=entity_type,
        description=description,
        request=request,
    )


async def log_login(db: AsyncSession, user: User, description: str, request: Optional[Request] = None):
    """Log a LOGIN action"""
    return await create_audit_log(
        db=db,
        action="login",
        user=user,
        description=description,
        request=request,
    )


async def log_api_action(db: AsyncSession, action: str, description: str, entity_type: Optional[str] = None, entity_id: Optional[int] = None, request: Optional[Request] = None):
    """Log an API or system action (no user)"""
    return await create_audit_log(
        db=db,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        request=request,
    )


async def log_action(session: AsyncSession, user_id: int, action: str, entity_type: str, entity_id: int, details: str, request: Optional[Request] = None):
    """Log a generic action with user_id (used by lead_conversion and other services)"""
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    return await create_audit_log(
        db=session,
        action=action,
        user=user,
        entity_type=entity_type,
        entity_id=entity_id,
        description=details,
        request=request,
    )
