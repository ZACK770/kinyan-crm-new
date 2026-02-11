"""Check users and promote to admin"""
import asyncio
from db import get_db, init_db
from sqlalchemy import text

async def main():
    await init_db()
    async for session in get_db():
        # List users
        r = await session.execute(text(
            "SELECT id, email, full_name, permission_level, is_active FROM users ORDER BY id"
        ))
        users = r.fetchall()
        print(f"{len(users)} users found:")
        for u in users:
            print(f"  id={u[0]} email={u[1]} name={u[2]} level={u[3]} active={u[4]}")
        
        if users:
            # Promote the latest user to admin + active
            latest = users[-1]
            print(f"\nPromoting user id={latest[0]} ({latest[1]}) to admin+active...")
            await session.execute(text(
                "UPDATE users SET permission_level=40, is_active=true WHERE id=:uid"
            ), {"uid": latest[0]})
            await session.commit()
            print("Done! You can now login.")

asyncio.run(main())
