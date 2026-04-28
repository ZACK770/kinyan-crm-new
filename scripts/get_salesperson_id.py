"""Get salesperson IDs by name"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from db import SessionLocal
    from db.models import Salesperson
    from sqlalchemy import select

    async with SessionLocal() as session:
        result = await session.execute(select(Salesperson.id, Salesperson.name))
        for row in result:
            print(f"{row.id}: {row.name}")

asyncio.run(main())
