"""
IVR Regulation Approval Webhook Handler.
Receives approval confirmation from IVR system when a student listens to and approves the regulations.
Updates the kinyan_signed checkbox in the student conversion tab and adds to lead history.

Expected payload format (similar to Yemot IVR):
{
    "ApiDID": "...",
    "ApiPhone": "0501234567",
    "ApiExtension": "...",
    "approval_confirmed": "1",
    "recording_url": "...",
    "timestamp": "...",
    ...additional IVR fields
}
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from services.leads import search_by_phone, add_interaction
from services.webhook_logger import log_webhook
from utils.phone import normalize_phone, is_valid_phone

router = APIRouter()


async def _parse_regulation_approval(data: dict) -> dict:
    """
    Parse IVR regulation approval webhook data.
    
    Args:
        data: Raw webhook payload from IVR system
        
    Returns:
        dict: Parsed data with phone, approval status, and metadata
    """
    # Extract phone number (try multiple field names)
    phone = data.get("ApiPhone") or data.get("phone") or data.get("Phone") or ""
    phone = normalize_phone(phone)
    
    if not phone or not is_valid_phone(phone):
        raise ValueError(f"Invalid or missing phone number: {phone}")
    
    # Check if approval was confirmed
    approval_confirmed = data.get("approval_confirmed") == "1" or data.get("approved") == "true"
    
    if not approval_confirmed:
        raise ValueError("Approval not confirmed in webhook data")
    
    # Extract additional metadata
    recording_url = data.get("recording_url") or data.get("RecordingUrl")
    ivr_extension = data.get("ApiExtension") or data.get("extension")
    ivr_did = data.get("ApiDID") or data.get("DID")
    timestamp_str = data.get("timestamp") or data.get("Timestamp")
    
    # Build notes with IVR details
    notes_parts = ["אישור תקנון התקבל מ-IVR"]
    if ivr_extension:
        notes_parts.append(f"שלוחה: {ivr_extension}")
    if ivr_did:
        notes_parts.append(f"DID: {ivr_did}")
    if recording_url:
        notes_parts.append(f"הקלטה: {recording_url}")
    if timestamp_str:
        notes_parts.append(f"זמן: {timestamp_str}")
    
    return {
        "phone": phone,
        "approval_confirmed": True,
        "recording_url": recording_url,
        "ivr_extension": ivr_extension,
        "ivr_did": ivr_did,
        "timestamp": timestamp_str,
        "notes": " | ".join(notes_parts)
    }


async def _process_regulation_approval(db: AsyncSession, parsed_data: dict) -> dict:
    """
    Process regulation approval: update lead and add interaction.
    
    Args:
        db: Database session
        parsed_data: Parsed webhook data
        
    Returns:
        dict: Processing result with success status and lead info
    """
    phone = parsed_data["phone"]
    
    # Find lead by phone
    lead = await search_by_phone(db, phone)
    
    if not lead:
        raise ValueError(f"Lead not found for phone: {phone}")
    
    # Update regulation approval fields
    lead.kinyan_signed = True
    lead.kinyan_signed_date = datetime.now(timezone.utc)
    lead.kinyan_method = "IVR"
    
    # Add notes with IVR details
    if parsed_data.get("notes"):
        lead.kinyan_notes = parsed_data["notes"]
    
    # Add interaction to lead history
    interaction_desc = f"אישור תקנון התקבל מ-IVR"
    if parsed_data.get("ivr_extension"):
        interaction_desc += f" (שלוחה {parsed_data['ivr_extension']})"
    
    interaction_data = {
        "interaction_type": "ivr_call",
        "call_status": "completed",
        "description": interaction_desc,
        "form_content": parsed_data.get("notes", "")
    }
    
    await add_interaction(db, lead.id, **interaction_data)
    await db.commit()
    
    return {
        "success": True,
        "lead_id": lead.id,
        "lead_name": lead.full_name,
        "phone": phone,
        "message": "Regulation approval processed successfully"
    }


@router.post("/תקנון/22")
async def regulation_approval_webhook(request: Request):
    """
    Webhook endpoint for IVR regulation approval.
    Path: /webhooks/תקנון/22
    
    Receives approval confirmation from IVR system, updates lead's kinyan_signed
    checkbox and adds interaction to history.
    """
    try:
        # Get raw payload
        raw_data = await request.json()
        
        # Parse the data
        parsed_data = await _parse_regulation_approval(raw_data)
        
        # Process in database
        async for db in get_db():
            result = await _process_regulation_approval(db, parsed_data)
            
            # Log successful webhook
            await log_webhook(
                db=db,
                source="ivr_regulation_approval",
                endpoint="/webhooks/תקנון/22",
                raw_payload=raw_data,
                parsed_data=parsed_data,
                success=True,
                result_data=result
            )
            
            return {
                "success": True,
                "message": "Regulation approval processed",
                "lead_id": result["lead_id"],
                "lead_name": result["lead_name"]
            }
    
    except ValueError as e:
        # Log failed webhook (validation error)
        async for db in get_db():
            await log_webhook(
                db=db,
                source="ivr_regulation_approval",
                endpoint="/webhooks/תקנון/22",
                raw_payload=raw_data if 'raw_data' in locals() else {},
                parsed_data={},
                success=False,
                error_message=str(e)
            )
        
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Log failed webhook (processing error)
        async for db in get_db():
            await log_webhook(
                db=db,
                source="ivr_regulation_approval",
                endpoint="/webhooks/תקנון/22",
                raw_payload=raw_data if 'raw_data' in locals() else {},
                parsed_data=parsed_data if 'parsed_data' in locals() else {},
                success=False,
                error_message=str(e)
            )
        
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
