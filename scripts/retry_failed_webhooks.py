"""
Retry failed elementor webhooks from webhook_logs.
Applies the same smartGet logic as the Make.com code to extract phone
from both Format A (flat: phone) and Format B (nested: field_6f8642e.value).
Then re-processes through the elementor handler.

Usage:
    python scripts/retry_failed_webhooks.py          # dry-run (show what would happen)
    python scripts/retry_failed_webhooks.py --run     # actually retry
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL", 
    "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new")

from sqlalchemy import select
from db import SessionLocal
from db.models import WebhookLog


def parse_raw(raw):
    """Parse raw_payload from DB (could be str or dict)."""
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except:
            return None
    return raw


def get_val(field):
    """Same as getVal in Make code — extract value from string or object."""
    if not field:
        return ""
    if isinstance(field, dict):
        return str(field.get("value") or field.get("raw_value") or "")
    return str(field)


def smart_get(data, *keys):
    """Same as smartGet in Make code — try multiple field names."""
    for key in keys:
        val = get_val(data.get(key))
        if val:
            return val
    return ""



# Manual phone overrides for leads where Make.com bug lost the phone entirely
# Format: webhook_log_id -> phone number
MANUAL_PHONE_OVERRIDES = {
    408: "0552804824",  # יצחק קליין
    409: "0552804824",  # יצחק קליין (duplicate)
    410: "0552804824",  # יצחק קליין (duplicate)
    412: "0555555555",  # נתנאל אליעזרי
    413: "0555555555",  # שלמה שכטר
    414: "0555555555",  # שאול סירוקה
    415: "0555555555",  # חיים צבי דושינסקי
}


def rebuild_payload(data, webhook_log_id=None):
    """
    Take the raw payload (as stored in DB) and rebuild it with the 
    smartGet logic — exactly like the Make.com code does.
    Handles both:
      Format A: {"phone": "053...", "name": "..."}
      Format B: {"field_6f8642e": {"value": "052..."}, "name": {"value": "..."}}
      Format C: flat elementor keys like {"fields[field_6f8642e][value]": "052..."}
    """
    if not isinstance(data, dict):
        return None, "Not a dict"

    # Check if this is already flat elementor format (keys like "fields[...][value]")
    is_flat = any(k.startswith("fields[") for k in data.keys())
    
    if is_flat:
        # Already in elementor format — try to extract phone from it
        phone = data.get("fields[field_6f8642e][value]", "")
        
        # Check manual overrides if phone is empty
        if not phone and webhook_log_id in MANUAL_PHONE_OVERRIDES:
            phone = MANUAL_PHONE_OVERRIDES[webhook_log_id]
            data = dict(data)  # copy so we don't mutate
            data["fields[field_6f8642e][value]"] = phone
            data["fields[field_6f8642e][raw_value]"] = phone
        
        if phone:
            return data, None  # Has phone, retry as-is
        # No phone in flat format — can't recover
        name = data.get("fields[name][value]", "?")
        email = data.get("fields[email][value]", "?")
        return None, f"No phone in flat payload. Name={name}, Email={email}"
    
    # Format A or B — apply smartGet logic
    phone   = smart_get(data, "phone", "field_6f8642e")
    name    = smart_get(data, "name")
    email   = smart_get(data, "email")
    course  = smart_get(data, "subject", "course", "field_fb4ae08")
    message = smart_get(data, "message", "field_b1e584d") or "no_notes"
    city    = smart_get(data, "city", "field_city")
    utm_src = smart_get(data, "utm_source")
    utm     = smart_get(data, "utm", "field_aab9d21")
    mkt     = smart_get(data, "marketing_product", "field_4c63868")

    if not phone:
        return None, f"No phone found anywhere. Name={name}, Email={email}"

    # Rebuild as flat elementor payload
    payload = {
        "form[id]": "b61ca57",
        "form[name]": "New Form",
        "fields[name][id]": "name",
        "fields[name][type]": "text",
        "fields[name][title]": "Name",
        "fields[name][value]": name,
        "fields[name][raw_value]": name,
        "fields[name][required]": "1",
        "fields[email][id]": "email",
        "fields[email][type]": "email",
        "fields[email][title]": "Email",
        "fields[email][value]": email,
        "fields[email][raw_value]": email,
        "fields[email][required]": "1",
        "fields[field_6f8642e][id]": "field_6f8642e",
        "fields[field_6f8642e][type]": "tel",
        "fields[field_6f8642e][title]": "טלפון",
        "fields[field_6f8642e][value]": phone,
        "fields[field_6f8642e][raw_value]": phone,
        "fields[field_6f8642e][required]": "1",
        "fields[field_fb4ae08][id]": "field_fb4ae08",
        "fields[field_fb4ae08][type]": "select",
        "fields[field_fb4ae08][title]": "בחר מסלול",
        "fields[field_fb4ae08][value]": course,
        "fields[field_fb4ae08][raw_value]": course,
        "fields[field_fb4ae08][required]": "1",
        "fields[field_b1e584d][id]": "field_b1e584d",
        "fields[field_b1e584d][type]": "textarea",
        "fields[field_b1e584d][title]": "תוכן ההודעה",
        "fields[field_b1e584d][value]": message,
        "fields[field_b1e584d][raw_value]": message,
        "fields[field_b1e584d][required]": "0",
        "fields[field_city][id]": "field_city",
        "fields[field_city][type]": "text",
        "fields[field_city][title]": "עיר",
        "fields[field_city][value]": city,
        "fields[field_city][raw_value]": city,
        "fields[field_city][required]": "0",
        "fields[field_32565c1][id]": "field_32565c1",
        "fields[field_32565c1][type]": "acceptance",
        "fields[field_32565c1][title]": "מאשר תוכן",
        "fields[field_32565c1][value]": "on",
        "fields[field_32565c1][raw_value]": "on",
        "fields[field_32565c1][required]": "1",
        "fields[utm_source][id]": "utm_source",
        "fields[utm_source][type]": "hidden",
        "fields[utm_source][title]": "מקור",
        "fields[utm_source][value]": utm_src,
        "fields[utm_source][raw_value]": utm_src,
        "fields[utm_source][required]": "0",
        "fields[field_aab9d21][id]": "field_aab9d21",
        "fields[field_aab9d21][type]": "hidden",
        "fields[field_aab9d21][title]": "UTM",
        "fields[field_aab9d21][value]": utm,
        "fields[field_aab9d21][raw_value]": utm,
        "fields[field_aab9d21][required]": "0",
        "fields[field_4c63868][id]": "field_4c63868",
        "fields[field_4c63868][type]": "hidden",
        "fields[field_4c63868][title]": "מוצר משווק",
        "fields[field_4c63868][value]": mkt,
        "fields[field_4c63868][raw_value]": mkt,
        "fields[field_4c63868][required]": "0",
        "meta[date][title]": "תאריך",
        "meta[date][value]": "",
        "meta[time][title]": "זמן",
        "meta[time][value]": "",
        "meta[page_url][title]": "קישור לעמוד",
        "meta[page_url][value]": "",
        "meta[user_agent][title]": "פרטי משתמש",
        "meta[user_agent][value]": "Retry Script",
        "meta[remote_ip][title]": "IP השולח",
        "meta[remote_ip][value]": "0.0.0.0",
        "meta[credit][title]": "מופעל באמצעות",
        "meta[credit][value]": "Retry Script",
    }
    return payload, None


async def main():
    dry_run = "--run" not in sys.argv
    
    if dry_run:
        print("=" * 60)
        print("DRY RUN — add --run to actually retry")
        print("=" * 60)
    else:
        print("=" * 60)
        print("LIVE RUN — retrying failed webhooks")
        print("=" * 60)

    async with SessionLocal() as db:
        stmt = select(WebhookLog).where(
            WebhookLog.webhook_type == "elementor",
            WebhookLog.success == False,
        ).order_by(WebhookLog.created_at.asc())
        result = await db.execute(stmt)
        failed = result.scalars().all()

    print(f"\nFound {len(failed)} failed elementor webhooks\n")

    retryable = []
    unrecoverable = []

    for wh in failed:
        raw = parse_raw(wh.raw_payload)
        if raw is None:
            unrecoverable.append((wh, "Cannot parse payload"))
            continue

        fixed, error = rebuild_payload(raw, webhook_log_id=wh.id)
        if fixed:
            retryable.append((wh, fixed))
        else:
            unrecoverable.append((wh, error))

    print(f"Retryable (have phone): {len(retryable)}")
    print(f"Unrecoverable (no phone): {len(unrecoverable)}")
    print()

    if unrecoverable:
        print("--- UNRECOVERABLE (need manual entry) ---")
        for wh, error in unrecoverable:
            print(f"  ID={wh.id} | {wh.created_at} | {error}")

    if retryable:
        print(f"\n--- {'WOULD RETRY' if dry_run else 'RETRYING'} {len(retryable)} webhooks ---")
        for wh, payload in retryable:
            name = payload.get("fields[name][value]", "?")
            phone = payload.get("fields[field_6f8642e][value]", "?")
            print(f"  ID={wh.id} | {name} | {phone}")

    if dry_run or not retryable:
        if dry_run and retryable:
            print(f"\nRun with --run to actually retry these {len(retryable)} webhooks.")
        return

    # Actually retry
    from webhooks.elementor import handle_elementor_webhook

    success_count = 0
    fail_count = 0

    async with SessionLocal() as db:
        for wh, payload in retryable:
            try:
                result = await handle_elementor_webhook(payload)
                if result.get("success"):
                    success_count += 1
                    print(f"  OK  ID={wh.id} | action={result.get('action')} | lead_id={result.get('lead_id')}")
                else:
                    fail_count += 1
                    print(f"  FAIL ID={wh.id} | error={result.get('error')}")
            except Exception as e:
                fail_count += 1
                print(f"  ERROR ID={wh.id} | {e}")

    print(f"\nDone! Success: {success_count}, Failed: {fail_count}")


if __name__ == "__main__":
    asyncio.run(main())
