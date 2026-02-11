"""
Webhooks API endpoints.
Routes incoming webhooks to the correct handler.
All webhooks are logged to WebhookLog for audit trail.

Supports:
- Elementor: Website form submissions → Lead creation
- Yemot: IVR call events from ימות המשיח → Lead creation
- Nedarim: Payment webhooks from נדרים פלוס → Payment status updates
- Generic: Manual/other sources → Lead creation
- Lesson Complete: Session ended → Update session, trigger recording
- Kinyan Approval: Terms approved via external link → Update lead
- File Upload: Auto-register file to entity → Create File record
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from webhooks.elementor import handle_elementor_webhook
from webhooks.yemot import handle_yemot_webhook
from webhooks.generic import handle_generic_webhook
from webhooks.nedarim import handle_nedarim_webhook
from webhooks.lesson_complete import handle_lesson_complete_webhook
from webhooks.kinyan_approval import handle_kinyan_approval_webhook
from webhooks.file_upload import handle_file_upload_webhook
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
    """Extract client IP from request (supports proxies)."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


async def _extract_data(request: Request) -> dict:
    """Extract data from request body (JSON or form-data) or query params for GET."""
    if request.method == "GET":
        return dict(request.query_params)
    content_type = request.headers.get("content-type", "")
    if "form" in content_type:
        return dict(await request.form())
    return await request.json()


# ============================================================
# Lead Ingestion Webhooks
# ============================================================

@router.api_route("/elementor", methods=["GET", "POST"])
async def elementor_webhook(request: Request):
    """Handle Elementor form submissions from website."""
    timer = WebhookTimer()
    data = None
    try:
        with timer:
            data = await _extract_data(request)
            data = _unwrap_array(data)
            logger.info(f"Elementor webhook received: phone={data.get('fields', {}).get('field_6f8642e', {}).get('value', 'N/A')}")
            result = await handle_elementor_webhook(data)
            logger.info(f"Elementor webhook result: {result}")
        
        # Log to DB
        async for db in get_db():
            await log_webhook(
                db, webhook_type="elementor", raw_payload=data,
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
                db, webhook_type="elementor", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False, error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db, webhook_log.id, "elementor", data,
                    _get_client_ip(request), str(e)
                )
            await db.commit()
        return {"success": False, "error": str(e)}


@router.api_route("/yemot", methods=["GET", "POST"])
async def yemot_webhook(request: Request):
    """Handle Yemot IVR call events."""
    timer = WebhookTimer()
    data = None
    try:
        with timer:
            data = await _extract_data(request)
            
            data = _unwrap_array(data)
            phone = data.get("Phone", data.get("phone", data.get("caller", "N/A")))
            logger.info(f"Yemot IVR webhook received: phone={phone}, folder={data.get('Folder', 'N/A')}")
            result = await handle_yemot_webhook(data)
            logger.info(f"Yemot webhook result: {result}")
        
        async for db in get_db():
            await log_webhook(
                db, webhook_type="yemot", raw_payload=data,
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
                db, webhook_type="yemot", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False, error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db, webhook_log.id, "yemot", data,
                    _get_client_ip(request), str(e)
                )
            await db.commit()
        return {"success": False, "error": str(e)}


@router.api_route("/generic", methods=["GET", "POST"])
async def generic_webhook(request: Request):
    """Handle generic webhook / manual API."""
    timer = WebhookTimer()
    data = None
    try:
        with timer:
            data = await _extract_data(request)
            result = await handle_generic_webhook(data)
        
        async for db in get_db():
            await log_webhook(
                db, webhook_type="generic", raw_payload=data,
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
        logger.error(f"Generic webhook error: {e}")
        async for db in get_db():
            webhook_log = await log_webhook(
                db, webhook_type="generic", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False, error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db, webhook_log.id, "generic", data,
                    _get_client_ip(request), str(e)
                )
            await db.commit()
        return {"success": False, "error": str(e)}


@router.api_route("/lead", methods=["GET", "POST"])
async def unified_lead_webhook(request: Request):
    """
    Unified lead ingestion endpoint.
    Auto-detects source (Elementor / Yemot IVR / Generic) and routes accordingly.
    
    This is the recommended endpoint for all lead webhooks.
    The legacy /elementor, /yemot, /generic endpoints still work for backward compatibility.
    """
    timer = WebhookTimer()
    data = None
    try:
        with timer:
            data = await _extract_data(request)
            data = _unwrap_array(data)
            source = detect_source(data)
            logger.info(f"Unified lead webhook: detected source={source}")
            result = await handle_unified_lead_webhook(data)
        
        async for db in get_db():
            await log_webhook(
                db, webhook_type=f"lead-unified:{result.get('source_detected', 'unknown')}",
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
                db, webhook_type="lead-unified", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False, error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db, webhook_log.id, "lead-unified", data,
                    _get_client_ip(request), str(e)
                )
            await db.commit()
        return {"success": False, "error": str(e)}


# ============================================================
# Payment Webhooks
# ============================================================

@router.api_route("/nedarim", methods=["GET", "POST"])
async def nedarim_webhook(request: Request):
    """
    Handle Nedarim Plus payment webhooks.
    Verifies signature and processes payment events.
    """
    timer = WebhookTimer()
    data = None
    try:
        with timer:
            # Get raw body for signature verification
            body = await request.body()
            signature = request.headers.get("X-Nedarim-Signature", "")
            
            # Verify signature
            if not verify_webhook_signature(body, signature):
                async for db in get_db():
                    await log_webhook(
                        db, webhook_type="nedarim", raw_payload=body.decode("utf-8", errors="replace"),
                        source_ip=_get_client_ip(request),
                        success=False, error_message="Invalid signature",
                    )
                    await db.commit()
                return {"success": False, "error": "Invalid signature"}
            
            data = await request.json()
            result = await handle_nedarim_webhook(data, signature)
        
        async for db in get_db():
            await log_webhook(
                db, webhook_type="nedarim", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=result.get("success", False),
                action=result.get("event_type"),
                result_data=result,
                entity_type="payment" if result.get("payment_id") else None,
                entity_id=result.get("payment_id"),
                processing_time_ms=timer.elapsed_ms,
            )
            await db.commit()
        
        return result
    except Exception as e:
        logger.error(f"Nedarim webhook error: {e}")
        async for db in get_db():
            webhook_log = await log_webhook(
                db, webhook_type="nedarim", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False, error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db, webhook_log.id, "nedarim", data,
                    _get_client_ip(request), str(e)
                )
            await db.commit()
        return {"success": False, "error": str(e)}


# ============================================================
# Lesson / Session Webhooks
# ============================================================

@router.api_route("/lesson-complete", methods=["GET", "POST"])
async def lesson_complete_webhook(request: Request):
    """
    Handle lesson completion events.
    Updates session status, saves recording URL, triggers post-lesson actions.
    
    Source: Yemot IVR, Zoom, or manual trigger.
    """
    timer = WebhookTimer()
    data = None
    try:
        with timer:
            data = await _extract_data(request)
            data = _unwrap_array(data)
            logger.info(f"Lesson complete webhook: session={data.get('session_id')}, module={data.get('module_id')}")
            result = await handle_lesson_complete_webhook(data)
        
        async for db in get_db():
            await log_webhook(
                db, webhook_type="lesson-complete", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=result.get("success", False),
                action=result.get("action"),
                result_data=result,
                entity_type="session" if result.get("session_id") else None,
                entity_id=result.get("session_id"),
                processing_time_ms=timer.elapsed_ms,
            )
            await db.commit()
        
        return result
    except Exception as e:
        logger.error(f"Lesson complete webhook error: {e}")
        async for db in get_db():
            webhook_log = await log_webhook(
                db, webhook_type="lesson-complete", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False, error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db, webhook_log.id, "lesson-complete", data,
                    _get_client_ip(request), str(e)
                )
            await db.commit()
        return {"success": False, "error": str(e)}


# ============================================================
# Terms / Kinyan Approval Webhooks
# ============================================================

@router.api_route("/kinyan-approval", methods=["GET", "POST"])
async def kinyan_approval_webhook(request: Request):
    """
    Handle kinyan/terms approval from external link.
    Updates lead's kinyan_signed status and related fields.
    
    Source: SMS link, email link, IVR confirmation.
    """
    timer = WebhookTimer()
    data = None
    try:
        with timer:
            data = await _extract_data(request)
            data = _unwrap_array(data)
            logger.info(f"Kinyan approval webhook: lead={data.get('lead_id')}, phone={data.get('phone')}")
            result = await handle_kinyan_approval_webhook(data)
        
        async for db in get_db():
            await log_webhook(
                db, webhook_type="kinyan-approval", raw_payload=data,
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
        logger.error(f"Kinyan approval webhook error: {e}")
        async for db in get_db():
            webhook_log = await log_webhook(
                db, webhook_type="kinyan-approval", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False, error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db, webhook_log.id, "kinyan-approval", data,
                    _get_client_ip(request), str(e)
                )
            await db.commit()
        return {"success": False, "error": str(e)}


# ============================================================
# File Upload Webhooks
# ============================================================

@router.api_route("/file-upload", methods=["GET", "POST"])
async def file_upload_webhook(request: Request):
    """
    Handle automatic file registration.
    Creates a File record linked to an entity (session, module, lead, student).
    
    Typically triggered after lesson recording is ready.
    """
    timer = WebhookTimer()
    data = None
    try:
        with timer:
            data = await _extract_data(request)
            data = _unwrap_array(data)
            logger.info(f"File upload webhook: entity={data.get('entity_type')}/{data.get('entity_id')}, file={data.get('filename')}")
            result = await handle_file_upload_webhook(data)
        
        async for db in get_db():
            await log_webhook(
                db, webhook_type="file-upload", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=result.get("success", False),
                action=result.get("action"),
                result_data=result,
                entity_type="file" if result.get("file_id") else None,
                entity_id=result.get("file_id"),
                processing_time_ms=timer.elapsed_ms,
            )
            await db.commit()
        
        return result
    except Exception as e:
        logger.error(f"File upload webhook error: {e}")
        async for db in get_db():
            webhook_log = await log_webhook(
                db, webhook_type="file-upload", raw_payload=data,
                source_ip=_get_client_ip(request),
                success=False, error_message=str(e),
                processing_time_ms=timer.elapsed_ms,
            )
            if webhook_log:
                await save_failed_webhook(
                    db, webhook_log.id, "file-upload", data,
                    _get_client_ip(request), str(e)
                )
            await db.commit()
        return {"success": False, "error": str(e)}


# ============================================================
# Webhook Status / Debug
# ============================================================

@router.get("/status")
async def webhook_status():
    """
    List all available webhook endpoints and their expected payloads.
    Useful for integration testing and documentation.
    """
    return {
        "webhooks": [
            {
                "endpoint": "/webhooks/lead",
                "method": "POST",
                "type": "lead_ingestion",
                "description": "★ Unified lead endpoint — auto-detects Elementor/Yemot/Generic and routes accordingly",
                "source": "Any (auto-detected)",
                "recommended": True,
            },
            {
                "endpoint": "/webhooks/elementor",
                "method": "POST",
                "type": "lead_ingestion",
                "description": "Elementor form submissions → Lead creation (legacy, use /lead instead)",
                "source": "Website forms",
            },
            {
                "endpoint": "/webhooks/yemot",
                "method": "POST",
                "type": "lead_ingestion",
                "description": "Yemot IVR call events → Lead creation (legacy, use /lead instead)",
                "source": "ימות המשיח IVR",
            },
            {
                "endpoint": "/webhooks/generic",
                "method": "POST",
                "type": "lead_ingestion",
                "description": "Generic/manual lead creation (legacy, use /lead instead)",
                "source": "API / Manual",
            },
            {
                "endpoint": "/webhooks/nedarim",
                "method": "POST",
                "type": "payment",
                "description": "Nedarim Plus payment events → Payment status updates",
                "source": "נדרים פלוס",
            },
            {
                "endpoint": "/webhooks/lesson-complete",
                "method": "POST",
                "type": "lesson",
                "description": "Lesson ended → Update session, trigger recording upload",
                "source": "Yemot / Zoom / Manual",
            },
            {
                "endpoint": "/webhooks/kinyan-approval",
                "method": "POST",
                "type": "approval",
                "description": "Terms/kinyan approved via external link → Update lead",
                "source": "SMS / Email / IVR",
            },
            {
                "endpoint": "/webhooks/file-upload",
                "method": "POST",
                "type": "file",
                "description": "Auto-register file to entity (recording, document)",
                "source": "Yemot / Storage / Manual",
            },
        ]
    }
