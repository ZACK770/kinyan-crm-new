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
from webhooks.nedarim_debitcard import handle_nedarim_debitcard_webhook
from webhooks.nedarim_keva import handle_nedarim_keva_webhook
from webhooks.lead_unified import handle_unified_lead_webhook, detect_source
from services.nedarim_plus import verify_webhook_signature
from services.webhook_logger import log_webhook, WebhookTimer
from services.webhook_queue import save_failed_webhook
from db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])


def _unwrap_array(data):
    """Unwrap array wrapper if data is a single-item array."""
    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return data


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, including proxy headers."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/elementor")
async def elementor_webhook(request: Request):
    """Handle Elementor form submissions from website."""
    timer = WebhookTimer()
    data = None

    try:
        with timer:
            # Elementor can send as form-data or JSON
            content_type = request.headers.get("content-type", "")
            if "form" in content_type:
                data = dict(await request.form())
            else:
                data = await request.json()

            data = _unwrap_array(data)
            logger.info(f"Elementor webhook received: phone={data.get('fields', {}).get('field_6f8642e', {}).get('value', 'N/A')}")
            result = await handle_elementor_webhook(data)
            logger.info(f"Elementor webhook result: {result}")

        async for db in get_db():
            await log_webhook(
                db,
                webhook_type="elementor",
                raw_payload=data,
                source_ip=_get_client_ip(request),
                success=result.get("success", False),
                action=result.get("action"),
                result_data=result,
                entity_type="lead" if result.get("lead_id") else None,
                entity_id=result.get("lead_id"),
                processing_time_ms=timer.elapsed_ms,
            )
            await db.commit()

        return result
    except Exception as e:
        logger.error(f"Elementor webhook error: {e}")
        async for db in get_db():
            webhook_log = await log_webhook(
                db,
                webhook_type="elementor",
                raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False,
                error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db,
                    webhook_log.id,
                    "elementor",
                    data,
                    _get_client_ip(request),
                    str(e),
                )
            await db.commit()

        return {"success": False, "error": str(e)}


@router.post("/yemot")
async def yemot_webhook(request: Request):
    """Handle Yemot IVR call events."""
    timer = WebhookTimer()
    data = None

    try:
        with timer:
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

        async for db in get_db():
            await log_webhook(
                db,
                webhook_type="yemot",
                raw_payload=data,
                source_ip=_get_client_ip(request),
                success=result.get("success", False),
                action=result.get("action"),
                result_data=result,
                entity_type="lead" if result.get("lead_id") else None,
                entity_id=result.get("lead_id"),
                processing_time_ms=timer.elapsed_ms,
            )
            await db.commit()

        return result
    except Exception as e:
        logger.error(f"Yemot webhook error: {e}")
        async for db in get_db():
            webhook_log = await log_webhook(
                db,
                webhook_type="yemot",
                raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False,
                error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db,
                    webhook_log.id,
                    "yemot",
                    data,
                    _get_client_ip(request),
                    str(e),
                )
            await db.commit()

        return {"success": False, "error": str(e)}


@router.post("/generic")
async def generic_webhook(request: Request):
    """Handle generic webhook / manual API."""
    data = await request.json()
    result = await handle_generic_webhook(data)
    return result


@router.get("/lead")
async def unified_lead_webhook_status(request: Request):
    """
    Public diagnostic endpoint for verifying the unified lead webhook is deployed.
    Also processes webhooks if query parameters are present (for systems like Yemot that use GET).
    """
    # If query params present, process as webhook
    if request.query_params:
        timer = WebhookTimer()
        data = None

        try:
            with timer:
                data = dict(request.query_params)
                logger.info(f"Unified lead webhook (GET with params): received {len(data)} query params")

                source = detect_source(data)
                logger.info(f"Unified lead webhook (GET with params): detected source={source}")
                result = await handle_unified_lead_webhook(data)

            async for db in get_db():
                await log_webhook(
                    db,
                    webhook_type=f"lead-unified:{result.get('source_detected', 'unknown')}",
                    raw_payload=data,
                    source_ip=_get_client_ip(request),
                    success=result.get("success", False),
                    action=result.get("action"),
                    result_data=result,
                    entity_type="lead" if result.get("lead_id") else None,
                    entity_id=result.get("lead_id"),
                    processing_time_ms=timer.elapsed_ms,
                )
                await db.commit()

            return result
        except Exception as e:
            logger.error(f"Unified lead webhook (GET with params) error: {e}")
            async for db in get_db():
                webhook_log = await log_webhook(
                    db,
                    webhook_type="lead-unified",
                    raw_payload=data,
                    source_ip=_get_client_ip(request),
                    success=False,
                    error_message=str(e),
                    processing_time_ms=timer.elapsed_ms,
                )
                if webhook_log:
                    await save_failed_webhook(
                        db,
                        webhook_log.id,
                        "lead-unified",
                        data,
                        _get_client_ip(request),
                        str(e),
                    )
                await db.commit()

            return {"success": False, "error": str(e)}

    # No query params - return diagnostic info
    return {
        "success": True,
        "endpoint": "/webhooks/lead",
        "methods": ["GET", "POST"],
        "status": "registered",
        "supports": ["elementor", "yemot", "generic"],
        "message": "Unified lead webhook is deployed. Use POST to submit lead payloads, or GET with query params for Yemot.",
    }


@router.post("/lead")
async def unified_lead_webhook(request: Request):
    """
    Unified lead ingestion endpoint.
    Auto-detects source (Elementor / Yemot IVR / Generic) and routes accordingly.
    """
    timer = WebhookTimer()
    data = None

    try:
        with timer:
            content_type = request.headers.get("content-type", "")
            if "form" in content_type:
                data = dict(await request.form())
            else:
                data = await request.json()

            data = _unwrap_array(data)
            source = detect_source(data)
            logger.info(f"Unified lead webhook: detected source={source}")
            result = await handle_unified_lead_webhook(data)

        async for db in get_db():
            await log_webhook(
                db,
                webhook_type=f"lead-unified:{result.get('source_detected', 'unknown')}",
                raw_payload=data,
                source_ip=_get_client_ip(request),
                success=result.get("success", False),
                action=result.get("action"),
                result_data=result,
                entity_type="lead" if result.get("lead_id") else None,
                entity_id=result.get("lead_id"),
                processing_time_ms=timer.elapsed_ms,
            )
            await db.commit()

        return result
    except Exception as e:
        logger.error(f"Unified lead webhook error: {e}")
        async for db in get_db():
            webhook_log = await log_webhook(
                db,
                webhook_type="lead-unified",
                raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False,
                error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db,
                    webhook_log.id,
                    "lead-unified",
                    data,
                    _get_client_ip(request),
                    str(e),
                )
            await db.commit()

        return {"success": False, "error": str(e)}


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


@router.post("/nedarim-debitcard")
async def nedarim_debitcard_webhook(request: Request):
    """
    Handle Nedarim Plus DebitCard API callbacks.
    These are direct credit card charges (RAGIL payments).
    Does NOT require signature verification (Nedarim doesn't sign these).
    """
    timer = WebhookTimer()
    data = None

    try:
        with timer:
            # Can be form-data or JSON
            content_type = request.headers.get("content-type", "")
            if "form" in content_type:
                data = dict(await request.form())
            else:
                data = await request.json()

            data = _unwrap_array(data)
            logger.info(f"Nedarim DebitCard webhook received: confirmation={data.get('Confirmation', 'N/A')}")

            async for db in get_db():
                result = await handle_nedarim_debitcard_webhook(db, data)
                await log_webhook(
                    db,
                    webhook_type="nedarim-debitcard",
                    raw_payload=data,
                    source_ip=_get_client_ip(request),
                    success=result.get("success", False),
                    action=result.get("action"),
                    result_data=result,
                    entity_type="payment" if result.get("payment_id") else None,
                    entity_id=result.get("payment_id"),
                    processing_time_ms=timer.elapsed_ms,
                )
                await db.commit()

            return result
    except Exception as e:
        logger.error(f"Nedarim DebitCard webhook error: {e}", exc_info=True)
        async for db in get_db():
            webhook_log = await log_webhook(
                db,
                webhook_type="nedarim-debitcard",
                raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False,
                error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db,
                    webhook_log.id,
                    "nedarim-debitcard",
                    data,
                    _get_client_ip(request),
                    str(e),
                )
            await db.commit()

        return {"success": False, "error": str(e)}


@router.post("/nedarim-keva")
async def nedarim_keva_webhook(request: Request):
    """
    Handle Nedarim Plus הוראת קבע (standing order) callbacks.
    These are recurring charges from Nedarim's keva system.
    Does NOT require signature verification (Nedarim doesn't sign these).
    """
    timer = WebhookTimer()
    data = None

    try:
        with timer:
            # Can be form-data or JSON
            content_type = request.headers.get("content-type", "")
            if "form" in content_type:
                data = dict(await request.form())
            else:
                data = await request.json()

            data = _unwrap_array(data)
            logger.info(f"Nedarim Keva webhook received: keva_id={data.get('KevaId', 'N/A')}, confirmation={data.get('Confirmation', 'N/A')}")

            async for db in get_db():
                result = await handle_nedarim_keva_webhook(db, data)
                await log_webhook(
                    db,
                    webhook_type="nedarim-keva",
                    raw_payload=data,
                    source_ip=_get_client_ip(request),
                    success=result.get("success", False),
                    action=result.get("action"),
                    result_data=result,
                    entity_type="payment" if result.get("payment_id") else None,
                    entity_id=result.get("payment_id"),
                    processing_time_ms=timer.elapsed_ms,
                )
                await db.commit()

            return result
    except Exception as e:
        logger.error(f"Nedarim Keva webhook error: {e}", exc_info=True)
        async for db in get_db():
            webhook_log = await log_webhook(
                db,
                webhook_type="nedarim-keva",
                raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False,
                error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db,
                    webhook_log.id,
                    "nedarim-keva",
                    data,
                    _get_client_ip(request),
                    str(e),
                )
            await db.commit()

        return {"success": False, "error": str(e)}
