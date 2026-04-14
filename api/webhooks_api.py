"""
Webhooks API endpoints.
Routes incoming webhooks to the correct handler.

Supports:
- Elementor: Website form submissions
- Yemot: IVR call events from ימות המשיח
- Nedarim: Payment webhooks from נדרים פלוס
- Generic: Manual/other sources
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from webhooks.elementor import handle_elementor_webhook
from webhooks.yemot import handle_yemot_webhook
from webhooks.generic import handle_generic_webhook
from webhooks.nedarim import handle_nedarim_webhook
from services.nedarim_plus import verify_webhook_signature

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])


def _unwrap_array(data):
    """Unwrap array wrapper if data is a single-item array."""
    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return data


@router.post("/elementor")
async def elementor_webhook(request: Request):
    """Handle Elementor form submissions from website."""
    try:
        data = await request.json()
        data = _unwrap_array(data)
        logger.info(f"Elementor webhook received: phone={data.get('fields', {}).get('field_6f8642e', {}).get('value', 'N/A')}")
        result = await handle_elementor_webhook(data)
        logger.info(f"Elementor webhook result: {result}")
        return result
    except Exception as e:
        logger.error(f"Elementor webhook error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/yemot")
async def yemot_webhook(request: Request):
    """Handle Yemot IVR call events."""
    try:
        # Yemot can send as form-data or JSON
        content_type = request.headers.get("content-type", "")
        if "form" in content_type:
            data = dict(await request.form())
        else:
            data = await request.json()
        
        data = _unwrap_array(data)
        phone = data.get("Phone", data.get("phone", data.get("caller", "N/A")))
        logger.info(f"Yemot IVR webhook received: phone={phone}, folder={data.get('Folder', 'N/A')}")
        result = await handle_yemot_webhook(data)
        logger.info(f"Yemot webhook result: {result}")
        return result
    except Exception as e:
        logger.error(f"Yemot webhook error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/generic")
async def generic_webhook(request: Request):
    """Handle generic webhook / manual API."""
    data = await request.json()
    result = await handle_generic_webhook(data)
    return result


@router.post("/nedarim")
async def nedarim_webhook(request: Request):
    """
    Handle Nedarim Plus payment webhooks.
    Verifies signature and processes payment events.
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Nedarim-Signature", "")
    
    # Verify signature
    if not verify_webhook_signature(body, signature):
        return {"success": False, "error": "Invalid signature"}
    
    data = await request.json()
    result = await handle_nedarim_webhook(data, signature)
    return result
