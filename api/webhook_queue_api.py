"""
Webhook Queue API endpoints.
Manage failed webhooks: list, retry, delete.
Admin only.
"""
import logging
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db import get_db
from db.models import WebhookQueue, WebhookLog, User
from services.webhook_queue import (
    get_queue_items,
    get_queue_item,
    delete_queue_item,
    mark_queue_item_status,
    increment_retry_count,
    cleanup_expired_queue_items,
)
from services.auth import get_current_user
from webhooks.elementor import handle_elementor_webhook
from webhooks.yemot import handle_yemot_webhook
from webhooks.generic import handle_generic_webhook
from webhooks.nedarim import handle_nedarim_webhook
from webhooks.lesson_complete import handle_lesson_complete_webhook
from webhooks.kinyan_approval import handle_kinyan_approval_webhook
from webhooks.file_upload import handle_file_upload_webhook
from webhooks.lead_unified import handle_unified_lead_webhook

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhook-queue", tags=["webhook-queue"])


def _check_admin(user: User):
    """Check if user is admin."""
    if user.permission_level < 40:
        raise HTTPException(status_code=403, detail="Admin access required")


async def _get_webhook_handler(webhook_type: str):
    """Get the appropriate handler for webhook type."""
    handlers = {
        "elementor": handle_elementor_webhook,
        "yemot": handle_yemot_webhook,
        "generic": handle_generic_webhook,
        "nedarim": handle_nedarim_webhook,
        "lesson-complete": handle_lesson_complete_webhook,
        "kinyan-approval": handle_kinyan_approval_webhook,
        "file-upload": handle_file_upload_webhook,
        "lead-unified": handle_unified_lead_webhook,
    }
    
    base_type = webhook_type.split(":")[0]
    return handlers.get(base_type)


@router.get("/list")
async def list_queue(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    status: Optional[str] = None,
    webhook_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    List failed webhooks in queue.
    Admin only.
    
    Query params:
    - status: pending/processing/success/failed/archived
    - webhook_type: elementor/yemot/nedarim/etc
    - limit: max items (default 50)
    - offset: pagination offset (default 0)
    """
    _check_admin(user)
    
    items, total = await get_queue_items(db, status=status, webhook_type=webhook_type, limit=limit, offset=offset)
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": item.id,
                "webhook_type": item.webhook_type,
                "status": item.status,
                "retry_count": item.retry_count,
                "max_retries": item.max_retries,
                "error_message": item.error_message,
                "last_error": item.last_error,
                "last_retry_at": item.last_retry_at.isoformat() if item.last_retry_at else None,
                "next_retry_at": item.next_retry_at.isoformat() if item.next_retry_at else None,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "expires_at": item.expires_at.isoformat() if item.expires_at else None,
            }
            for item in items
        ],
    }


@router.get("/stats")
async def queue_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get queue statistics.
    Admin only.
    """
    _check_admin(user)
    
    stmt = select(func.count(WebhookQueue.id)).where(WebhookQueue.status == "pending")
    pending = await db.execute(stmt)
    pending_count = pending.scalar() or 0
    
    stmt = select(func.count(WebhookQueue.id)).where(WebhookQueue.status == "failed")
    failed = await db.execute(stmt)
    failed_count = failed.scalar() or 0
    
    stmt = select(func.count(WebhookQueue.id)).where(WebhookQueue.status == "processing")
    processing = await db.execute(stmt)
    processing_count = processing.scalar() or 0
    
    stmt = select(WebhookQueue.webhook_type, func.count(WebhookQueue.id)).group_by(WebhookQueue.webhook_type)
    by_type = await db.execute(stmt)
    by_type_dict = {row[0]: row[1] for row in by_type.all()}
    
    return {
        "success": True,
        "pending": pending_count,
        "failed": failed_count,
        "processing": processing_count,
        "by_type": by_type_dict,
    }


@router.get("/{queue_id}")
async def get_queue_item_detail(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get details of a queue item.
    Admin only.
    """
    _check_admin(user)
    
    item = await get_queue_item(db, queue_id)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    try:
        raw_payload = json.loads(item.raw_payload) if isinstance(item.raw_payload, str) else item.raw_payload
    except:
        raw_payload = item.raw_payload
    
    return {
        "success": True,
        "item": {
            "id": item.id,
            "webhook_type": item.webhook_type,
            "status": item.status,
            "retry_count": item.retry_count,
            "max_retries": item.max_retries,
            "error_message": item.error_message,
            "last_error": item.last_error,
            "raw_payload": raw_payload,
            "source_ip": item.source_ip,
            "last_retry_at": item.last_retry_at.isoformat() if item.last_retry_at else None,
            "next_retry_at": item.next_retry_at.isoformat() if item.next_retry_at else None,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
            "expires_at": item.expires_at.isoformat() if item.expires_at else None,
        },
    }


@router.post("/{queue_id}/retry")
async def retry_webhook(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retry a failed webhook.
    Admin only.
    """
    _check_admin(user)
    
    item = await get_queue_item(db, queue_id)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    await mark_queue_item_status(db, queue_id, "processing")
    await db.commit()
    
    try:
        raw_payload = json.loads(item.raw_payload) if isinstance(item.raw_payload, str) else item.raw_payload
        
        handler = await _get_webhook_handler(item.webhook_type)
        if not handler:
            raise ValueError(f"No handler for webhook type: {item.webhook_type}")
        
        result = await handler(raw_payload)
        
        if result.get("success"):
            await mark_queue_item_status(db, queue_id, "success")
            await db.commit()
            logger.info(f"Webhook retry successful: {queue_id}")
            return {
                "success": True,
                "message": "Webhook retried successfully",
                "result": result,
            }
        else:
            error_msg = result.get("error", "Unknown error")
            await increment_retry_count(db, queue_id, error_msg)
            await db.commit()
            logger.warning(f"Webhook retry failed: {queue_id} - {error_msg}")
            return {
                "success": False,
                "message": "Webhook retry failed",
                "error": error_msg,
                "retry_count": item.retry_count + 1,
                "max_retries": item.max_retries,
            }
    
    except Exception as e:
        error_msg = str(e)
        await increment_retry_count(db, queue_id, error_msg)
        await db.commit()
        logger.error(f"Error retrying webhook {queue_id}: {e}")
        return {
            "success": False,
            "message": "Error retrying webhook",
            "error": error_msg,
            "retry_count": item.retry_count + 1,
            "max_retries": item.max_retries,
        }


@router.delete("/{queue_id}")
async def delete_queue_item_endpoint(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete a queue item.
    Admin only.
    """
    _check_admin(user)
    
    success = await delete_queue_item(db, queue_id)
    if not success:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    await db.commit()
    return {"success": True, "message": "Queue item deleted"}


@router.post("/cleanup")
async def cleanup_queue(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Clean up expired queue items (older than 30 days).
    Admin only.
    """
    _check_admin(user)
    
    count = await cleanup_expired_queue_items(db)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Cleaned up {count} expired items",
        "deleted_count": count,
    }


@router.post("/{queue_id}/archive")
async def archive_queue_item(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Archive a queue item (mark as archived).
    Admin only.
    """
    _check_admin(user)
    
    item = await mark_queue_item_status(db, queue_id, "archived")
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    await db.commit()
    return {
        "success": True,
        "message": "Queue item archived",
        "item": {
            "id": item.id,
            "status": item.status,
        },
    }
