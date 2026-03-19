"""Check what's actually stored in raw_payload for failed elementor webhooks."""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL",
    "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new")

from sqlalchemy import select
from db import SessionLocal
from db.models import WebhookLog


async def main():
    async with SessionLocal() as db:
        stmt = select(WebhookLog).where(
            WebhookLog.webhook_type == "elementor",
            WebhookLog.success == False,
        ).order_by(WebhookLog.created_at.desc()).limit(20)
        result = await db.execute(stmt)
        rows = result.scalars().all()

    print(f"Found {len(rows)} failed elementor webhooks\n")

    for wh in rows:
        raw = wh.raw_payload
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except:
                print(f"ID={wh.id} | CANNOT PARSE")
                continue

        # Show ALL keys that might contain phone
        print(f"=== ID={wh.id} | {wh.created_at} | err={wh.error_message or ''} ===")
        
        if isinstance(raw, dict):
            # Check flat elementor format
            flat_phone = raw.get("fields[field_6f8642e][value]", "(not present)")
            flat_name = raw.get("fields[name][value]", "(not present)")
            
            # Check nested/object format  
            field_6f = raw.get("field_6f8642e", "(not present)")
            phone_key = raw.get("phone", "(not present)")
            name_key = raw.get("name", "(not present)")
            
            print(f"  flat phone: [{flat_phone}]")
            print(f"  flat name:  [{flat_name}]")
            print(f"  field_6f8642e: [{field_6f}]")
            print(f"  phone: [{phone_key}]")
            print(f"  name:  [{name_key}]")
            
            # Show all keys for debugging
            keys = list(raw.keys())[:15]
            print(f"  first keys: {keys}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
