"""
Inbound Email Webhook — receives email batches from Make.com (Gmail sync).
Endpoint: POST /webhooks/inbound-email
"""
import time
import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, settings
from services.inbound_emails import process_email_batch
from services.webhook_logger import log_webhook, WebhookTimer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/inbound-email")
async def receive_inbound_emails(
    request: Request,
    key: str = Query(None, description="API key for authentication"),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive a batch of emails from Make.com webhook.
    Expects a JSON array of email objects (Gmail format).
    Supports both single email object and array of emails.
    """
    # Auth check
    api_key = key or request.headers.get("X-API-Key", "")
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(401, "Invalid API key")

    timer = WebhookTimer()
    with timer:
        try:
            body = await request.json()

            # Support both single object and array
            if isinstance(body, dict):
                emails = [body]
            elif isinstance(body, list):
                emails = body
            else:
                raise HTTPException(400, "Expected JSON array or object")

            if len(emails) == 0:
                return {"status": "ok", "detail": "Empty batch", "created": 0}

            result = await process_email_batch(db, emails)
            await db.commit()

            # Log webhook
            await log_webhook(
                db=db,
                webhook_type="inbound-email",
                raw_payload={"batch_size": len(emails), "first_id": emails[0].get("id", "?")},
                source_ip=request.client.host if request.client else "",
                parsed_data=result,
                success=True,
                action="processed",
                result_data=result,
                processing_time_ms=timer.elapsed_ms,
            )
            await db.commit()

            logger.info(
                f"Inbound email webhook: {result['created']} created, "
                f"{result['skipped']} skipped, {result['errors']} errors "
                f"(batch of {len(emails)})"
            )

            return {
                "status": "ok",
                "detail": f"Processed {len(emails)} emails",
                **result,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Inbound email webhook error: {e}")
            import traceback
            traceback.print_exc()

            # Log failure
            try:
                await log_webhook(
                    db=db,
                    webhook_type="inbound-email",
                    raw_payload=str(e),
                    source_ip=request.client.host if request.client else "",
                    success=False,
                    action="failed",
                    error_message=str(e),
                    processing_time_ms=timer.elapsed_ms,
                )
                await db.commit()
            except Exception:
                pass

            raise HTTPException(500, f"Error processing emails: {str(e)}")
