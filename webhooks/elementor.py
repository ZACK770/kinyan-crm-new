"""
Elementor form webhook handler.
Parses incoming lead data from Elementor forms submitted on the website.
"""
from db import get_db
from services.leads import process_incoming_lead

# Field mapping: Elementor field names → our field names
FIELD_MAP = {
    "שם מלא": "name",
    "name": "name",
    "שם": "name",
    "טלפון": "phone",
    "phone": "phone",
    "נייד": "phone",
    "אימייל": "email",
    "email": "email",
    "עיר": "city",
    "city": "city",
    "הודעה": "source_message",
    "message": "source_message",
}


def parse_elementor_payload(data: dict) -> dict:
    """
    Parse Elementor form submission into normalized lead data.
    Supports various form field naming conventions.
    """
    parsed = {
        "source_type": "elementor",
        "interaction_type": "form",
    }

    # Try to extract from structured fields (array of {id, value})
    fields = data.get("fields", [])
    if isinstance(fields, list):
        for field in fields:
            field_id = str(field.get("id", "")).strip()
            field_name = str(field.get("name", field_id)).strip()
            value = str(field.get("value", "")).strip()
            if not value:
                continue

            # Try mapping by name
            mapped = FIELD_MAP.get(field_name) or FIELD_MAP.get(field_id)
            if mapped:
                parsed[mapped] = value
    elif isinstance(fields, dict):
        for key, value in fields.items():
            mapped = FIELD_MAP.get(key)
            if mapped:
                parsed[mapped] = str(value).strip()

    # Also check top-level keys
    for key, mapped in FIELD_MAP.items():
        if key in data and mapped not in parsed:
            parsed[mapped] = str(data[key]).strip()

    # Source details
    parsed["source_name"] = data.get("form_name", data.get("form_id", "elementor"))
    parsed["source_details"] = data.get("page_url", "")

    # Campaign from UTM
    utm_source = data.get("utm_source", "")
    utm_campaign = data.get("utm_campaign", "")
    if utm_campaign:
        parsed["campaign_name"] = utm_campaign
    elif utm_source:
        parsed["campaign_name"] = utm_source

    return parsed


async def handle_elementor_webhook(data: dict) -> dict:
    """Process an Elementor webhook end-to-end."""
    parsed = parse_elementor_payload(data)
    async for db in get_db():
        result = await process_incoming_lead(db, **parsed)
        return result
    return {"success": False, "error": "DB session error"}
