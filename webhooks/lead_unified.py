"""
Unified Lead Ingestion webhook handler.
Auto-detects source (Elementor / Yemot IVR / Generic) and routes to the correct parser.

Single endpoint: POST /webhooks/lead

Detection logic:
- Has "fields" + "form" keys → Elementor website form
- Has "Phone" or "Folder" or "QueueStatus" → Yemot IVR
- Otherwise → Generic flat format
"""
import logging

from webhooks.elementor import parse_elementor_payload
from webhooks.yemot import parse_yemot_payload
from webhooks.generic import parse_generic_payload
from db import get_db
from services.leads import process_incoming_lead

logger = logging.getLogger(__name__)


def detect_source(data: dict) -> str:
    """
    Auto-detect the webhook source based on payload structure.
    
    Returns: "elementor" | "yemot" | "generic"
    """
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    # Elementor: has "fields" dict/list + "form" metadata
    if "fields" in data and ("form" in data or "meta" in data):
        return "elementor"
    
    # Yemot IVR: has Phone/Folder/QueueStatus/CustomerDID
    yemot_keys = {"Phone", "Folder", "QueueStatus", "CustomerDID", "AnswerNumber", "ApiPhone", "ApiExtension"}
    if any(k in data for k in yemot_keys):
        return "yemot"
    
    # Generic fallback
    return "generic"


def parse_by_source(data: dict, source: str) -> dict:
    """Route to the correct parser based on detected source."""
    if source == "elementor":
        return parse_elementor_payload(data)
    elif source == "yemot":
        return parse_yemot_payload(data)
    else:
        return parse_generic_payload(data)


async def handle_unified_lead_webhook(data: dict) -> dict:
    """
    Process a lead webhook from any source.
    
    Flow:
    1. Detect source (elementor/yemot/generic)
    2. Parse payload using source-specific parser
    3. Call process_incoming_lead (create or update)
    4. Return result with source info
    """
    # Handle array wrapper
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    # Detect and parse
    source = detect_source(data)
    parsed = parse_by_source(data, source)
    
    logger.info(f"Unified lead webhook: source={source}, phone={parsed.get('phone', 'N/A')}")
    
    async for db in get_db():
        result = await process_incoming_lead(db, **parsed)
        result["source_detected"] = source
        return result
    
    return {"success": False, "error": "DB session error"}
