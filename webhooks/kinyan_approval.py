"""
Kinyan/Terms Approval webhook handler.
Triggered when a lead approves terms/kinyan via external link (SMS, email, IVR).

Expected payload:
{
    "lead_id": 123,                    # Lead ID
    "phone": "0527109371",             # Phone for verification (alternative to lead_id)
    "method": "sms",                   # אישור טלפוני / SMS / מייל / חתימה דיגיטלית / IVR
    "file_url": "https://...",         # Signed PDF URL (optional)
    "notes": "...",                    # Additional notes
    "token": "abc123",                # Verification token (optional, for secure links)
    "timestamp": "2026-02-11T14:00:00"
}
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import Lead
from utils.phone import normalize_phone, is_valid_phone

logger = logging.getLogger(__name__)


def parse_kinyan_approval_payload(data: dict) -> dict:
    """Parse and normalize kinyan approval webhook data."""
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    return {
        "lead_id": data.get("lead_id"),
        "phone": data.get("phone", ""),
        "method": data.get("method", "webhook"),
        "file_url": data.get("file_url"),
        "notes": data.get("notes"),
        "token": data.get("token"),
    }


async def _find_lead(db: AsyncSession, parsed: dict) -> Optional[Lead]:
    """Find lead by ID or phone."""
    if parsed.get("lead_id"):
        stmt = select(Lead).where(Lead.id == parsed["lead_id"])
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()
        if lead:
            return lead
    
    if parsed.get("phone") and is_valid_phone(parsed["phone"]):
        phone = normalize_phone(parsed["phone"])
        stmt = select(Lead).where(Lead.phone == phone).limit(1)
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()
        if lead:
            return lead
    
    return None


async def handle_kinyan_approval_webhook(data: dict) -> dict:
    """
    Process a kinyan/terms approval webhook.
    
    Flow:
    1. Find the lead
    2. Mark kinyan as signed
    3. Save method, date, file URL
    4. Update lead status if needed
    """
    parsed = parse_kinyan_approval_payload(data)
    
    async for db in get_db():
        try:
            lead = await _find_lead(db, parsed)
            
            if not lead:
                return {
                    "success": False,
                    "error": "Lead not found",
                    "parsed": parsed,
                }
            
            # Already signed?
            if lead.kinyan_signed:
                return {
                    "success": True,
                    "action": "already_signed",
                    "lead_id": lead.id,
                    "message": "תקנון כבר אושר",
                }
            
            # Mark kinyan as signed
            lead.kinyan_signed = True
            lead.kinyan_signed_date = datetime.now()
            lead.kinyan_method = parsed["method"]
            
            if parsed["file_url"]:
                lead.kinyan_file_url = parsed["file_url"]
            if parsed["notes"]:
                lead.kinyan_notes = parsed["notes"]
            
            # Also update the legacy approved_terms field
            lead.approved_terms = True
            lead.approval_method = parsed["method"]
            lead.approval_date = datetime.now()
            
            await db.flush()
            await db.commit()
            
            result = {
                "success": True,
                "action": "kinyan_approved",
                "lead_id": lead.id,
                "method": parsed["method"],
                "message": f"תקנון אושר עבור ליד #{lead.id} ({lead.full_name})",
            }
            
            logger.info(f"Kinyan approved: lead {lead.id} via {parsed['method']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing kinyan approval webhook: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "DB session error"}
