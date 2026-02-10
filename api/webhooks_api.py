"""
Webhooks API endpoints.
Routes incoming webhooks to the correct handler.
"""
from fastapi import APIRouter, Request
from webhooks.elementor import handle_elementor_webhook
from webhooks.yemot import handle_yemot_webhook
from webhooks.generic import handle_generic_webhook

router = APIRouter(tags=["webhooks"])


@router.post("/elementor")
async def elementor_webhook(request: Request):
    """Handle Elementor form submissions."""
    data = await request.json()
    result = await handle_elementor_webhook(data)
    return result


@router.post("/yemot")
async def yemot_webhook(request: Request):
    """Handle Yemot IVR call events."""
    # Yemot can send as form-data or JSON
    content_type = request.headers.get("content-type", "")
    if "form" in content_type:
        data = dict(await request.form())
    else:
        data = await request.json()
    result = await handle_yemot_webhook(data)
    return result


@router.post("/generic")
async def generic_webhook(request: Request):
    """Handle generic webhook / manual API."""
    data = await request.json()
    result = await handle_generic_webhook(data)
    return result
