"""
Webhook queue service.
Manages failed webhooks and retry logic.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from db.models import WebhookQueue, WebhookLog

logger = logging.getLogger(__name__)


async def save_failed_webhook(
    db: AsyncSession,
    webhook_log_id: int,
    webhook_type: str,
    raw_payload: Any,
    source_ip: Optional[str],
    error_message: str,
) -> WebhookQueue:
    """
    Save a failed webhook to the queue for retry.
    
    Args:
        db: Database session
        webhook_log_id: ID of the WebhookLog entry
        webhook_type: Type of webhook (elementor/yemot/nedarim/etc)
        raw_payload: Raw incoming data
        source_ip: Source IP address
        error_message: Error message from processing
    
    Returns:
        Created WebhookQueue entry
    """
    try:
        payload_str = json.dumps(raw_payload, ensure_ascii=False, default=str) if not isinstance(raw_payload, str) else raw_payload
        
        expires_at = datetime.now(datetime.now().astimezone().tzinfo) + timedelta(days=30)
        
        queue_entry = WebhookQueue(
            webhook_log_id=webhook_log_id,
            webhook_type=webhook_type,
            raw_payload=payload_str,
            source_ip=source_ip,
            error_message=error_message,
            status="pending",
            expires_at=expires_at,
        )
        db.add(queue_entry)
        await db.flush()
        
        logger.info(f"Failed webhook saved to queue: {webhook_type} (ID: {queue_entry.id})")
        return queue_entry
    except Exception as e:
        logger.error(f"Failed to save webhook to queue: {e}")
        raise


async def get_queue_items(
    db: AsyncSession,
    status: Optional[str] = None,
    webhook_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[List[WebhookQueue], int]:
    """
    Get queue items with optional filtering.
    
    Args:
        db: Database session
        status: Filter by status (pending/processing/success/failed/archived)
        webhook_type: Filter by webhook type
        limit: Number of items to return
        offset: Pagination offset
    
    Returns:
        Tuple of (queue items, total count)
    """
    filters = []
    
    if status:
        filters.append(WebhookQueue.status == status)
    if webhook_type:
        filters.append(WebhookQueue.webhook_type == webhook_type)
    
    filters.append(WebhookQueue.expires_at > datetime.now(datetime.now().astimezone().tzinfo))
    
    query = select(WebhookQueue)
    if filters:
        query = query.where(and_(*filters))
    
    count_query = select(WebhookQueue)
    if filters:
        count_query = count_query.where(and_(*filters))
    
    count_result = await db.execute(select(func.count()).select_from(WebhookQueue).where(and_(*filters) if filters else True))
    total_count = count_result.scalar() or 0
    
    result = await db.execute(query.order_by(WebhookQueue.created_at.desc()).limit(limit).offset(offset))
    items = result.scalars().all()
    
    return items, total_count


async def get_queue_item(db: AsyncSession, queue_id: int) -> Optional[WebhookQueue]:
    """Get a single queue item by ID."""
    stmt = select(WebhookQueue).where(WebhookQueue.id == queue_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_queue_item(db: AsyncSession, queue_id: int) -> bool:
    """Delete a queue item."""
    item = await get_queue_item(db, queue_id)
    if not item:
        return False
    
    await db.delete(item)
    await db.flush()
    logger.info(f"Deleted webhook queue item: {queue_id}")
    return True


async def mark_queue_item_status(
    db: AsyncSession,
    queue_id: int,
    status: str,
    error: Optional[str] = None,
) -> Optional[WebhookQueue]:
    """
    Update status of a queue item.
    
    Args:
        db: Database session
        queue_id: Queue item ID
        status: New status (pending/processing/success/failed/archived)
        error: Error message if failed
    
    Returns:
        Updated queue item or None if not found
    """
    item = await get_queue_item(db, queue_id)
    if not item:
        return None
    
    item.status = status
    item.updated_at = datetime.now(datetime.now().astimezone().tzinfo)
    
    if error:
        item.last_error = error
    
    if status == "success":
        item.retry_count = 0
    
    await db.flush()
    return item


async def increment_retry_count(
    db: AsyncSession,
    queue_id: int,
    error_message: Optional[str] = None,
) -> Optional[WebhookQueue]:
    """
    Increment retry count and set next retry time.
    
    Args:
        db: Database session
        queue_id: Queue item ID
        error_message: Error message from failed retry
    
    Returns:
        Updated queue item or None if not found
    """
    item = await get_queue_item(db, queue_id)
    if not item:
        return None
    
    item.retry_count += 1
    item.last_retry_at = datetime.now(datetime.now().astimezone().tzinfo)
    
    if error_message:
        item.last_error = error_message
    
    if item.retry_count >= item.max_retries:
        item.status = "failed"
    else:
        backoff_seconds = min(300, 30 * (2 ** item.retry_count))
        item.next_retry_at = datetime.now(datetime.now().astimezone().tzinfo) + timedelta(seconds=backoff_seconds)
        item.status = "pending"
    
    item.updated_at = datetime.now(datetime.now().astimezone().tzinfo)
    await db.flush()
    return item


async def cleanup_expired_queue_items(db: AsyncSession) -> int:
    """
    Delete expired queue items (older than 30 days).
    
    Returns:
        Number of deleted items
    """
    cutoff_date = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(days=30)
    stmt = select(WebhookQueue).where(WebhookQueue.created_at < cutoff_date)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    count = len(items)
    for item in items:
        await db.delete(item)
    
    if count > 0:
        await db.flush()
        logger.info(f"Cleaned up {count} expired webhook queue items")
    
    return count
