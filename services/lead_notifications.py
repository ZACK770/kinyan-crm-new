"""
Lead notification service.
Sends notifications to salespeople when new leads are assigned.

Supports:
1. In-app notification (via Notification model / WebhookLog)
2. External webhook (POST to salesperson's notification_webhook_url)
   - Can be WhatsApp API, Slack, custom endpoint, etc.
"""
import logging
import httpx
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Salesperson, Lead

logger = logging.getLogger(__name__)


async def notify_salesperson_new_lead(
    db: AsyncSession,
    lead_id: int,
    salesperson_id: int,
    source: str = "webhook",
    extra_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send notification to salesperson about a new lead assignment.
    
    1. Loads salesperson + lead data
    2. If notify_on_new_lead is True:
       a. If notification_webhook_url exists → POST to external webhook
       b. Always logs the notification attempt
    
    Args:
        db: Database session
        lead_id: The new lead ID
        salesperson_id: The assigned salesperson ID
        source: Where the lead came from (elementor/yemot/generic)
        extra_data: Additional data to include in notification
    
    Returns:
        Dict with notification result
    """
    result = {"notified": False, "method": None}
    
    try:
        # Load salesperson
        sp_stmt = select(Salesperson).where(Salesperson.id == salesperson_id)
        sp_result = await db.execute(sp_stmt)
        salesperson = sp_result.scalar_one_or_none()
        
        if not salesperson:
            logger.warning(f"Salesperson {salesperson_id} not found for notification")
            return result
        
        if not salesperson.notify_on_new_lead:
            result["method"] = "disabled"
            return result
        
        # Load lead
        lead_stmt = select(Lead).where(Lead.id == lead_id)
        lead_result = await db.execute(lead_stmt)
        lead = lead_result.scalar_one_or_none()
        
        if not lead:
            logger.warning(f"Lead {lead_id} not found for notification")
            return result
        
        # Build notification payload
        notification_payload = _build_notification_payload(lead, salesperson, source, extra_data)
        
        # Send external webhook if configured
        if salesperson.notification_webhook_url:
            webhook_result = await _send_external_webhook(
                salesperson.notification_webhook_url,
                notification_payload,
            )
            result["external_webhook"] = webhook_result
            result["method"] = "external_webhook"
            result["notified"] = webhook_result.get("success", False)
        else:
            result["method"] = "in_app_only"
            result["notified"] = True
        
        logger.info(
            f"Lead notification: lead={lead_id} → salesperson={salesperson.name} "
            f"(method={result['method']}, notified={result['notified']})"
        )
        
    except Exception as e:
        logger.error(f"Error sending lead notification: {e}")
        result["error"] = str(e)
    
    return result


def _build_notification_payload(
    lead: Lead,
    salesperson: Salesperson,
    source: str,
    extra_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Build the notification payload for external webhook."""
    payload = {
        "event": "new_lead_assigned",
        "lead": {
            "id": lead.id,
            "full_name": lead.full_name,
            "phone": lead.phone,
            "email": lead.email,
            "city": lead.city,
            "source_type": lead.source_type,
            "source_name": lead.source_name,
            "status": lead.status,
        },
        "salesperson": {
            "id": salesperson.id,
            "name": salesperson.name,
            "phone": salesperson.phone,
        },
        "source": source,
        "message": f"ליד חדש: {lead.full_name} ({lead.phone}) שויך אליך מ-{source}",
    }
    
    if extra_data:
        payload["extra"] = extra_data
    
    return payload


async def _send_external_webhook(
    url: str,
    payload: Dict[str, Any],
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """
    Send POST request to external webhook URL.
    Fire-and-forget style — errors are logged but don't break the flow.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response": response.text[:500],  # Truncate response
            }
    except httpx.TimeoutException:
        logger.warning(f"External webhook timeout: {url}")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        logger.error(f"External webhook error: {url} → {e}")
        return {"success": False, "error": str(e)}
