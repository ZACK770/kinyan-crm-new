"""
WhatsApp webhook handler for Green-API (incomingMessageReceived).
"""
import logging
from db import get_db
from services.leads import process_incoming_lead

logger = logging.getLogger(__name__)

def parse_whatsapp_payload(data: dict) -> dict:
    """
    Parses Green-API WhatsApp webhook payload.
    Expected structure:
    {
        "typeWebhook": "incomingMessageReceived",
        "senderData": {
            "sender": "972527180504@c.us",
            "senderName": "אייזיק קליין"
        },
        "messageData": {
            "textMessageData": {
                "textMessage": "..."
            }
        }
    }
    """
    sender_data = data.get("senderData", {})
    message_data = data.get("messageData", {})
    
    # Try different text fields in Green-API payload
    text = ""
    
    # 1. Standard text message
    text_data = message_data.get("textMessageData", {})
    text = text_data.get("textMessage", "")
    
    # 2. Extended text message (links, quotes, etc)
    if not text:
        extended_data = message_data.get("extendedTextMessageData", {})
        text = extended_data.get("text", "")
        
    # 3. Caption (for images/files)
    if not text:
        text = message_data.get("caption", "")

    # Extract phone and strip @c.us suffix
    sender = sender_data.get("sender", "")
    phone = sender.split("@")[0] if "@" in sender else sender
    
    return {
        "name": sender_data.get("senderName", ""),
        "phone": phone,
        "source_type": "whatsapp",
        "source_name": "whatsapp",
        "source_message": text,
        "interaction_type": "whatsapp_message",
        "description": text if text else "הודעת וואטסאפ (ללא טקסט)"
    }

async def handle_whatsapp_webhook(data: dict) -> dict:
    """Process a WhatsApp webhook."""
    # Green-API can send different types of webhooks, we only care about incomingMessageReceived for leads
    webhook_type = data.get("typeWebhook")
    if webhook_type != "incomingMessageReceived":
        logger.info(f"Ignoring WhatsApp webhook type: {webhook_type}")
        return {"success": True, "action": "ignored", "type": webhook_type}

    parsed = parse_whatsapp_payload(data)
    
    if not parsed["phone"]:
        return {"success": False, "error": "No phone number found in payload"}
        
    async for db in get_db():
        result = await process_incoming_lead(db, **parsed)
        return result
        
    return {"success": False, "error": "DB session error"}
