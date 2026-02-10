"""
Yemot HaMashiach (ימות המשיח) IVR webhook handler.
Parses incoming call data from the IVR system.

Replaces make_code_module_ivr.js (479 lines JS → ~90 lines Python)
"""
from db import get_db
from services.leads import process_incoming_lead

# IVR folder → product mapping (from JS: FOLDER_TO_PRODUCT)
FOLDER_TO_PRODUCT = {
    "1": "שבת",
    "2": "איסור והיתר",
    "3": "טהרה",
    "4": "ממונות",
}


def parse_yemot_payload(data: dict) -> dict:
    """
    Parse Yemot IVR webhook.
    Yemot sends 'caller', 'hangupCause', 'ivr2_choice', etc.
    """
    parsed = {
        "source_type": "yemot",
        "interaction_type": "call",
    }

    # Phone number
    caller = data.get("ApiPhone", data.get("caller", data.get("phone", "")))
    parsed["phone"] = caller

    # Call status
    cause = data.get("hangupCause", data.get("ApiHangupCause", ""))
    parsed["call_status"] = _map_hangup_cause(cause)

    # Wait time / duration
    parsed["wait_time"] = data.get("ApiWaitTime", data.get("waitTime"))
    parsed["call_duration"] = data.get("ApiDuration", data.get("duration"))
    parsed["total_duration"] = data.get("ApiTotalDuration", data.get("totalDuration"))

    # IVR extension (determines product of interest)
    ext = str(data.get("ApiExtension", data.get("ivr2_choice", data.get("extension", ""))))
    folder = ext.split("/")[0] if ext else ""
    product = FOLDER_TO_PRODUCT.get(folder, "")
    if product:
        parsed["ivr_product"] = product
        parsed["form_product"] = product

    # Caller name (if known)
    parsed["user_name"] = data.get("ApiCallerId", data.get("callerName", ""))

    # Did the caller actually reach someone?
    real_ext = data.get("ApiRealExtension", data.get("realExtension", ""))
    parsed["source_details"] = f"ext={ext} real={real_ext} cause={cause}"
    parsed["source_name"] = "yemot"

    return parsed


def _map_hangup_cause(cause: str) -> str:
    """Map Yemot hangup cause to Hebrew status."""
    cause_map = {
        "NORMAL_CLEARING": "שיחה תקינה",
        "NO_ANSWER": "לא ענה",
        "BUSY": "תפוס",
        "CANCEL": "בוטלה",
        "CONGESTION": "עומס",
        "": "לא ידוע",
    }
    return cause_map.get(cause.upper() if cause else "", cause or "לא ידוע")


async def handle_yemot_webhook(data: dict) -> dict:
    """Process a Yemot IVR webhook end-to-end."""
    parsed = parse_yemot_payload(data)
    async for db in get_db():
        result = await process_incoming_lead(db, **parsed)
        return result
    return {"success": False, "error": "DB session error"}
