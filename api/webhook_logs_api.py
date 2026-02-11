"""
Webhook Logs API endpoints.
View and filter webhook logs for monitoring and debugging.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import WebhookLog
from .dependencies import require_permission

router = APIRouter(tags=["webhook-logs"])


# ── Schemas ────────────────────────────────────────
class WebhookLogResponse(BaseModel):
    id: int
    webhook_type: str
    source_ip: str | None
    success: bool
    action: str | None
    error_message: str | None
    entity_type: str | None
    entity_id: int | None
    processing_time_ms: int | None
    created_at: str
    raw_payload: str | None = None
    result_data: str | None = None


class WebhookLogsStats(BaseModel):
    total_webhooks: int
    successful: int
    failed: int
    by_type: dict[str, int]
    avg_processing_time_ms: float | None


# ── Endpoints ────────────────────────────────────────
@router.get("/", response_model=list[WebhookLogResponse])
async def list_webhook_logs(
    webhook_type: str | None = Query(None, description="סנן לפי סוג webhook"),
    success: bool | None = Query(None, description="סנן לפי הצלחה/כשלון"),
    entity_type: str | None = Query(None, description="סנן לפי סוג ישות"),
    hours: int = Query(24, description="כמה שעות אחורה להציג", ge=1, le=720),
    limit: int = Query(100, description="מקסימום תוצאות", ge=1, le=1000),
    include_payload: bool = Query(False, description="כולל payload מלא"),
    user = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Get webhook logs with filters."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    stmt = (
        select(WebhookLog)
        .where(WebhookLog.created_at >= since)
        .order_by(desc(WebhookLog.created_at))
        .limit(limit)
    )
    
    if webhook_type:
        stmt = stmt.where(WebhookLog.webhook_type == webhook_type)
    if success is not None:
        stmt = stmt.where(WebhookLog.success == success)
    if entity_type:
        stmt = stmt.where(WebhookLog.entity_type == entity_type)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return [
        WebhookLogResponse(
            id=log.id,
            webhook_type=log.webhook_type,
            source_ip=log.source_ip,
            success=log.success,
            action=log.action,
            error_message=log.error_message,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            processing_time_ms=log.processing_time_ms,
            created_at=log.created_at.isoformat(),
            raw_payload=log.raw_payload if include_payload else None,
            result_data=log.result_data if include_payload else None,
        )
        for log in logs
    ]


@router.get("/stats", response_model=WebhookLogsStats)
async def get_webhook_stats(
    hours: int = Query(24, description="כמה שעות אחורה לחשב", ge=1, le=720),
    user = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Get webhook statistics."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Total count
    total_stmt = select(func.count()).select_from(WebhookLog).where(WebhookLog.created_at >= since)
    total = (await db.execute(total_stmt)).scalar() or 0
    
    # Success count
    success_stmt = (
        select(func.count())
        .select_from(WebhookLog)
        .where(WebhookLog.created_at >= since)
        .where(WebhookLog.success == True)  # noqa: E712
    )
    successful = (await db.execute(success_stmt)).scalar() or 0
    
    # By type
    by_type_stmt = (
        select(WebhookLog.webhook_type, func.count())
        .where(WebhookLog.created_at >= since)
        .group_by(WebhookLog.webhook_type)
    )
    by_type_result = await db.execute(by_type_stmt)
    by_type = {row[0]: row[1] for row in by_type_result.all()}
    
    # Average processing time
    avg_time_stmt = (
        select(func.avg(WebhookLog.processing_time_ms))
        .where(WebhookLog.created_at >= since)
        .where(WebhookLog.processing_time_ms.isnot(None))
    )
    avg_time = (await db.execute(avg_time_stmt)).scalar()
    
    return WebhookLogsStats(
        total_webhooks=total,
        successful=successful,
        failed=total - successful,
        by_type=by_type,
        avg_processing_time_ms=float(avg_time) if avg_time else None,
    )


@router.get("/{log_id}", response_model=WebhookLogResponse)
async def get_webhook_log(
    log_id: int,
    user = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific webhook log with full payload."""
    stmt = select(WebhookLog).where(WebhookLog.id == log_id)
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()
    
    if not log:
        from fastapi import HTTPException
        raise HTTPException(404, "Webhook log not found")
    
    return WebhookLogResponse(
        id=log.id,
        webhook_type=log.webhook_type,
        source_ip=log.source_ip,
        success=log.success,
        action=log.action,
        error_message=log.error_message,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        processing_time_ms=log.processing_time_ms,
        created_at=log.created_at.isoformat(),
        raw_payload=log.raw_payload,
        result_data=log.result_data,
    )
