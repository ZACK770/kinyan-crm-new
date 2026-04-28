"""Get salesperson IDs from remote DB"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    # Set the DATABASE_URL temporarily
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
    
    from db import SessionLocal
    from db.models import Salesperson
    from sqlalchemy import select

    async with SessionLocal() as session:
        result = await session.execute(select(Salesperson.id, Salesperson.name).order_by(Salesperson.id))
        print("=== Salespeople in DB ===")
        for row in result:
            print(f"ID: {row.id}, Name: {row.name}")

if __name__ == "__main__":
    asyncio.run(main())
