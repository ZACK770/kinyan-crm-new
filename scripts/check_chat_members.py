"""Check chat thread memberships in DB."""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"

from sqlalchemy import select, text
from db import SessionLocal
from db.models import ChatThread, ChatThreadMember, User


async def main():
    async with SessionLocal() as db:
        # Get all threads
        threads = (await db.execute(select(ChatThread).order_by(ChatThread.id))).scalars().all()
        print(f"\n=== {len(threads)} threads ===\n")
        
        for t in threads:
            members_result = await db.execute(
                select(ChatThreadMember, User.full_name, User.email)
                .join(User, User.id == ChatThreadMember.user_id)
                .where(ChatThreadMember.thread_id == t.id)
            )
            members = members_result.all()
            
            print(f"Thread #{t.id}: type={t.thread_type}, title={t.title}, is_sales_team={t.is_sales_team}")
            for m, name, email in members:
                print(f"  - user_id={m.user_id}: {name} ({email})")
            print()


asyncio.run(main())
