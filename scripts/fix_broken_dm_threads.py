"""Fix broken DM threads that have only 1 member (created by dev user id=0)."""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"

from sqlalchemy import select, func, delete
from db import SessionLocal
from db.models import ChatThread, ChatThreadMember, ChatMessage


async def main():
    async with SessionLocal() as db:
        # Find DM threads with less than 2 members
        stmt = (
            select(ChatThread.id, func.count(ChatThreadMember.id).label("cnt"))
            .outerjoin(ChatThreadMember, ChatThreadMember.thread_id == ChatThread.id)
            .where(ChatThread.thread_type == "dm")
            .group_by(ChatThread.id)
            .having(func.count(ChatThreadMember.id) < 2)
        )
        result = await db.execute(stmt)
        broken = result.all()

        if not broken:
            print("No broken DM threads found.")
            return

        broken_ids = [row[0] for row in broken]
        print(f"Found {len(broken_ids)} broken DM threads: {broken_ids}")

        # Delete messages in broken threads
        del_msgs = await db.execute(delete(ChatMessage).where(ChatMessage.thread_id.in_(broken_ids)))
        print(f"Deleted {del_msgs.rowcount} messages from broken threads")

        # Delete members
        del_members = await db.execute(delete(ChatThreadMember).where(ChatThreadMember.thread_id.in_(broken_ids)))
        print(f"Deleted {del_members.rowcount} memberships from broken threads")

        # Delete threads
        del_threads = await db.execute(delete(ChatThread).where(ChatThread.id.in_(broken_ids)))
        print(f"Deleted {del_threads.rowcount} broken DM threads")

        await db.commit()
        print("Done!")


asyncio.run(main())
