"""
Nedarim Plus webhook handler.
Processes incoming payment notifications from Nedarim Plus.
"""
import logging
from typing import Dict, Any

from db import get_db
from services import nedarim_plus

logger = logging.getLogger(__name__)


async def handle_nedarim_webhook(data: Dict[str, Any], signature: str = "") -> Dict[str, Any]:
    """
    Handle incoming Nedarim Plus webhook.
    
    Args:
        data: Webhook payload
        signature: X-Nedarim-Signature header value for verification
    
    Returns:
        Processing result dict
    """
    logger.info(f"Received Nedarim webhook: {data.get('event_type')}")
    
    async for db in get_db():
        try:
            result = await nedarim_plus.process_webhook(db, data)
            await db.commit()
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Error processing Nedarim webhook: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "DB session error"}
