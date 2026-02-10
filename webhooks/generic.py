"""
Generic webhook handler for custom / test integrations.
"""
from db import get_db
from services.leads import process_incoming_lead


def parse_generic_payload(data: dict) -> dict:
    """Flat mapping of standardized fields."""
    return {
        "name": data.get("name", data.get("full_name", "")),
        "phone": data.get("phone", ""),
        "email": data.get("email"),
        "city": data.get("city"),
        "source_type": data.get("source_type", "generic"),
        "source_name": data.get("source_name", "api"),
        "campaign_name": data.get("campaign_name"),
        "source_message": data.get("message"),
        "interaction_type": data.get("interaction_type", "generic"),
    }


async def handle_generic_webhook(data: dict) -> dict:
    """Process a generic webhook."""
    parsed = parse_generic_payload(data)
    async for db in get_db():
        result = await process_incoming_lead(db, **parsed)
        return result
    return {"success": False, "error": "DB session error"}
