"""
Yemot HaMashiach (ימות המשיח) IVR webhook handler.
Parses incoming call data from the IVR system.

Example Yemot webhook payload:
{
    "CustomerDID": "0795792345",
    "Phone": "0527109371",        # Caller's phone
    "Date": "10/02/2026",
    "Time": "14:29:44",
    "Folder": "99999/2",          # Extension - /2 means product 2
    "QueueStatus": "CONTINUE",
    "AnswerSeconds": "1300",      # Total call time in seconds
    "AnswerTime": "0:21:40",
    "AnswerNumber": "0527635459", # Who answered
    ...
}

Replaces make_code_module_ivr.js (479 lines JS → ~100 lines Python)
"""
from datetime import datetime
from db import get_db
from services.leads import process_incoming_lead

# IVR folder → product mapping (extension number to course/product)
# Key is the extension number (after the /)
FOLDER_TO_PRODUCT = {
    "1": "שבת",
    "2": "איסור והיתר",
    "3": "טהרה",
    "4": "ממונות",
    "5": "נזיקין",
    "6": "סמיכה",
}


def parse_yemot_payload(data: dict) -> dict:
    """
    Parse Yemot IVR webhook.
    Handles both the new format (Phone, Folder, etc.) and legacy format.
    """
    # Handle array wrapper
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
        
    parsed = {
        "source_type": "yemot",
        "interaction_type": "ivr_call",
        "source_name": "yemot",
    }

    # Phone number - try multiple possible field names
    phone = (
        data.get("Phone") or 
        data.get("phone") or 
        data.get("ApiPhone") or 
        data.get("caller") or 
        ""
    )
    parsed["phone"] = phone

    # Caller name (if known) - also add as name for lead creation
    caller_name = data.get("ApiCallerId", data.get("callerName", ""))
    parsed["user_name"] = caller_name
    parsed["name"] = caller_name or "ליד ימות"  # Default name if not provided

    # IVR extension/folder (determines product of interest)
    folder = data.get("Folder", data.get("folder", data.get("ApiExtension", data.get("extension", ""))))
    folder = str(folder)
    
    # Extract extension number from folder path (e.g., "99999/2" → "2")
    if "/" in folder:
        parts = folder.split("/")
        ext_num = parts[-1] if parts[-1].isdigit() else parts[0]
    else:
        ext_num = folder
    
    product = FOLDER_TO_PRODUCT.get(ext_num, "")
    if product:
        parsed["ivr_product"] = product
        parsed["form_product"] = product
        parsed["requested_course"] = product

    # Call answered status
    queue_status = data.get("QueueStatus", data.get("hangupCause", data.get("ApiHangupCause", "")))
    answer_number = data.get("AnswerNumber", data.get("answerNumber", ""))
    
    # Determine if call was answered
    if answer_number or queue_status in ("CONTINUE", "ANSWERED"):
        parsed["call_status"] = "נענה"
    else:
        parsed["call_status"] = _map_hangup_cause(queue_status)

    # Wait time before answer
    wait_time = (
        data.get("QueueWaitingTime") or 
        data.get("QueueWaitingSeconds") or 
        data.get("ApiWaitTime") or 
        data.get("waitTime") or 
        ""
    )
    parsed["wait_time"] = str(wait_time)

    # Answer/call duration
    answer_time = (
        data.get("AnswerTime") or
        data.get("AnswerSeconds") or
        data.get("ApiDuration") or 
        data.get("duration") or 
        ""
    )
    parsed["call_duration"] = str(answer_time)

    # Total queue time
    total_time = (
        data.get("QueueTotalTime") or 
        data.get("QueueTotalSeconds") or 
        data.get("ApiTotalDuration") or 
        data.get("totalDuration") or 
        ""
    )
    parsed["total_duration"] = str(total_time)

    # Build source details
    date_str = data.get("Date", "")
    time_str = data.get("Time", "")
    hebrew_date = data.get("HebrewDate", "")
    answered_by = answer_number or ""
    
    details_parts = []
    if date_str:
        details_parts.append(f"תאריך: {date_str}")
    if time_str:
        details_parts.append(f"שעה: {time_str}")
    if hebrew_date:
        details_parts.append(f"({hebrew_date})")
    if answered_by:
        details_parts.append(f"ענה: {answered_by}")
    if folder:
        details_parts.append(f"שלוחה: {folder}")
        
    parsed["source_details"] = " | ".join(details_parts)

    return parsed


def _map_hangup_cause(cause: str) -> str:
    """Map Yemot hangup cause to Hebrew status."""
    if not cause:
        return "לא ידוע"
        
    cause_upper = cause.upper()
    cause_map = {
        "NORMAL_CLEARING": "שיחה תקינה",
        "NO_ANSWER": "לא ענה",
        "BUSY": "תפוס",
        "CANCEL": "בוטלה",
        "CONGESTION": "עומס",
        "CONTINUE": "נענה",
        "ANSWERED": "נענה",
    }
    return cause_map.get(cause_upper, cause or "לא ידוע")


async def handle_yemot_webhook(data: dict) -> dict:
    """Process a Yemot IVR webhook end-to-end."""
    parsed = parse_yemot_payload(data)
    async for db in get_db():
        result = await process_incoming_lead(db, **parsed)
        return result
    return {"success": False, "error": "DB session error"}
