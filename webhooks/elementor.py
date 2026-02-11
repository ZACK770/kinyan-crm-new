"""
Elementor form webhook handler.
Parses incoming lead data from Elementor forms submitted on the website.

Supports the standard Elementor webhook format where fields is a dict of objects:
{
    "form": {"id": "xxx", "name": "Form Name"},
    "fields": {
        "field_id": {"id": "xxx", "type": "text", "title": "שם", "value": "..."},
        ...
    },
    "meta": {"date": {...}, "time": {...}, "page_url": {...}}
}
"""
from datetime import datetime
from db import get_db
from services.leads import process_incoming_lead

# Field mapping: Elementor field titles → our field names
FIELD_MAP = {
    # Hebrew titles
    "שם מלא": "name",
    "שם": "name",
    "name": "name",
    "טלפון": "phone",
    "phone": "phone",
    "נייד": "phone",
    "אימייל": "email",
    "email": "email",
    "עיר": "city",
    "city": "city",
    "הודעה": "source_message",
    "תוכן ההודעה": "source_message",
    "message": "source_message",
    # Product selection
    "בחר מסלול": "form_product",
    "מוצר": "form_product",
    "קורס": "form_product",
    # UTM fields
    "מקור": "utm_source",
    "utm_source": "utm_source",
    "utm": "utm_data",
    "מוצר משווק": "marketing_product",
}


def _unflatten_elementor_data(data: dict) -> dict:
    """
    Convert flat Elementor format to nested format.
    
    Input: {"fields[name][value]": "John", "fields[name][title]": "Name", "form[id]": "123"}
    Output: {"fields": {"name": {"value": "John", "title": "Name"}}, "form": {"id": "123"}}
    """
    # Check if data is already in flat format
    has_flat_keys = any(k.startswith(("fields[", "form[", "meta[")) for k in data.keys())
    if not has_flat_keys:
        return data
    
    nested = {}
    
    for key, value in data.items():
        # Parse keys like "fields[name][value]" or "form[id]"
        if "[" not in key:
            nested[key] = value
            continue
        
        parts = key.replace("]", "").split("[")
        
        # Build nested structure
        current = nested
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the final value
        current[parts[-1]] = value
    
    return nested


def parse_elementor_payload(data: dict) -> dict:
    """
    Parse Elementor form submission into normalized lead data.
    Supports various form field naming conventions and formats.
    
    Format 1: fields as dict of objects (new Elementor format)
    Format 2: fields as array of {id, value} objects
    Format 3: flat key-value pairs
    Format 4: flat format with keys like "fields[name][value]", "form[id]"
    """
    parsed = {
        "source_type": "elementor",
        "interaction_type": "website_form",
    }

    # Handle array wrapper (webhook might send as array with single item)
    if isinstance(data, list) and len(data) > 0:
        data = data[0]

    # Convert flat format to nested if needed
    data = _unflatten_elementor_data(data)

    # Extract form metadata
    form_info = data.get("form", {})
    if form_info:
        parsed["source_name"] = form_info.get("name", form_info.get("id", "elementor"))
    
    # Extract fields
    fields = data.get("fields", {})
    
    # Format 1: dict of field objects (e.g., {"field_id": {"title": "שם", "value": "..."}})
    if isinstance(fields, dict):
        for field_key, field_obj in fields.items():
            if not isinstance(field_obj, dict):
                # Simple key-value
                _map_field(parsed, field_key, str(field_obj))
                continue
                
            title = str(field_obj.get("title", field_key)).strip()
            value = str(field_obj.get("value", field_obj.get("raw_value", ""))).strip()
            
            if not value or value == "on":  # Skip empty or boolean acceptance fields
                if field_obj.get("type") == "acceptance":
                    continue
                    
            _map_field(parsed, title, value)
            
            # Also try by field ID
            field_id = str(field_obj.get("id", field_key)).strip()
            if field_id != title:
                _map_field(parsed, field_id, value)
    
    # Format 2: array of field objects
    elif isinstance(fields, list):
        for field in fields:
            if not isinstance(field, dict):
                continue
            field_id = str(field.get("id", "")).strip()
            field_name = str(field.get("name", field_id)).strip()
            value = str(field.get("value", "")).strip()
            if not value:
                continue
            _map_field(parsed, field_name, value) or _map_field(parsed, field_id, value)

    # Also check top-level keys
    for key, mapped in FIELD_MAP.items():
        if key in data and mapped not in parsed:
            parsed[mapped] = str(data[key]).strip()

    # Extract meta info (date, time, page_url)
    meta = data.get("meta", {})
    if meta:
        page_url_info = meta.get("page_url", {})
        if isinstance(page_url_info, dict):
            parsed["source_details"] = page_url_info.get("value", "")
        elif isinstance(page_url_info, str):
            parsed["source_details"] = page_url_info
        
        # Parse date/time
        date_info = meta.get("date", {})
        time_info = meta.get("time", {})
        if date_info and time_info:
            date_str = date_info.get("value", "") if isinstance(date_info, dict) else str(date_info)
            time_str = time_info.get("value", "") if isinstance(time_info, dict) else str(time_info)
            parsed["form_content"] = f"תאריך: {date_str}, שעה: {time_str}"

    # Campaign from UTM
    utm_source = parsed.pop("utm_source", "") or ""
    utm_data = parsed.pop("utm_data", "") or ""
    marketing_product = parsed.pop("marketing_product", "") or ""
    
    if utm_source:
        parsed["campaign_name"] = utm_source
    if utm_data:
        parsed["source_details"] = (parsed.get("source_details", "") + f" UTM: {utm_data}").strip()
    if marketing_product:
        parsed["form_product"] = parsed.get("form_product") or marketing_product

    return parsed


def _map_field(parsed: dict, field_name: str, value: str) -> bool:
    """Map a field name to our internal field name if recognized."""
    field_name_lower = field_name.lower().strip()
    for key, mapped in FIELD_MAP.items():
        if key.lower() == field_name_lower or key == field_name:
            if mapped not in parsed or not parsed[mapped]:
                parsed[mapped] = value
            return True
    return False


async def handle_elementor_webhook(data: dict) -> dict:
    """Process an Elementor webhook end-to-end."""
    parsed = parse_elementor_payload(data)
    async for db in get_db():
        result = await process_incoming_lead(db, **parsed)
        return result
    return {"success": False, "error": "DB session error"}
