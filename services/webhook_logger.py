"""
Webhook logging service.
Provides centralized logging for all incoming webhooks with audit trail.
"""
import json
import time
import logging
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from db.models import WebhookLog

logger = logging.getLogger(__name__)


async def log_webhook(
    db: AsyncSession,
    webhook_type: str,
    raw_payload: Any,
    source_ip: str = "",
    parsed_data: Optional[Dict] = None,
    success: bool = False,
    action: Optional[str] = None,
    result_data: Optional[Dict] = None,
    error_message: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    processing_time_ms: Optional[int] = None,
) -> WebhookLog:
    """
    Log a webhook event to the database.
    
    Args:
        db: Database session
        webhook_type: Type of webhook (elementor/yemot/generic/nedarim/lesson-complete/kinyan-approval/file-upload)
        raw_payload: Raw incoming data (will be JSON-serialized)
        source_ip: IP address of the sender
        parsed_data: Normalized/parsed data dict
        success: Whether processing succeeded
        action: What action was taken (created/updated/processed/failed)
        result_data: Processing result dict
        error_message: Error message if failed
        entity_type: Type of entity affected (lead/payment/session/file)
        entity_id: ID of entity affected
        processing_time_ms: Processing time in milliseconds
    """
    try:
        log_entry = WebhookLog(
            webhook_type=webhook_type,
            source_ip=source_ip,
            raw_payload=_safe_json(raw_payload),
            parsed_data=_safe_json(parsed_data) if parsed_data else None,
            success=success,
            action=action,
            result_data=_safe_json(result_data) if result_data else None,
            error_message=error_message,
            entity_type=entity_type,
            entity_id=entity_id,
            processing_time_ms=processing_time_ms,
        )
        db.add(log_entry)
        await db.flush()
        return log_entry
    except Exception as e:
        logger.error(f"Failed to log webhook: {e}")
        # Don't let logging failure break the webhook processing
        return None


class WebhookTimer:
    """Context manager to measure webhook processing time."""
    
    def __init__(self):
        self.start_time = None
        self.elapsed_ms = 0
    
    def __enter__(self):
        self.start_time = time.monotonic()
        return self
    
    def __exit__(self, *args):
        self.elapsed_ms = int((time.monotonic() - self.start_time) * 1000)


def _safe_json(data: Any) -> str:
    """Safely serialize data to JSON string, handling non-serializable types."""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        return str(data)
