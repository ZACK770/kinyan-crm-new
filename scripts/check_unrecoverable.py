"""Check the 'unrecoverable' webhooks - see if they have phone somewhere."""
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
    # IDs that were marked unrecoverable
    unrecoverable_ids = [408, 409, 410, 412, 413, 414, 415, 416, 417, 418, 419]
    
    async with SessionLocal() as db:
        stmt = select(WebhookLog).where(WebhookLog.id.in_(unrecoverable_ids))
        result = await db.execute(stmt)
        rows = result.scalars().all()

    for wh in sorted(rows, key=lambda x: x.id):
        raw = wh.raw_payload
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except:
                print(f"ID={wh.id} | CANNOT PARSE")
                continue

        print(f"=== ID={wh.id} | {wh.created_at} ===")
        print(f"  error: {wh.error_message or '(none)'}")
        
        # Show full payload to find phone anywhere
        if isinstance(raw, dict):
            # Search for anything that looks like a phone in ALL values
            for k, v in raw.items():
                v_str = str(v)
                # Look for phone-like patterns
                if any(c.isdigit() for c in v_str) and len(v_str) >= 7:
                    print(f"  {k}: {v_str}")
                elif "phone" in k.lower() or "tel" in k.lower() or "6f8642e" in k:
                    print(f"  {k}: [{v_str}]")
            
            # Also check if there are matching successful webhooks by name
            name = raw.get("fields[name][value]", "")
            email = raw.get("fields[email][value]", "")
            print(f"  NAME={name} | EMAIL={email}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
