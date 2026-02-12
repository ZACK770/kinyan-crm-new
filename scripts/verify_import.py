"""Verify that created_at dates were imported correctly from Excel"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from db import SessionLocal
    from db.models import Lead
    from sqlalchemy import select, func

    async with SessionLocal() as session:
        # Total leads
        total = (await session.execute(select(func.count(Lead.id)))).scalar()
        print(f"Total leads in DB: {total}")

        # Sample 10 leads — show created_at
        result = await session.execute(
            select(Lead.id, Lead.full_name, Lead.phone, Lead.created_at, Lead.arrival_date, Lead.status)
            .order_by(Lead.id.desc())
            .limit(10)
        )
        print("\nLast 10 leads:")
        for row in result:
            print(f"  ID={row.id} | {row.full_name} | {row.phone} | created_at={row.created_at} | arrival={row.arrival_date} | status={row.status}")

        # Check how many have created_at != today
        from datetime import datetime, timezone, timedelta
        today = datetime.now(timezone.utc).date()
        not_today = (await session.execute(
            select(func.count(Lead.id)).where(func.date(Lead.created_at) != today)
        )).scalar()
        is_today = (await session.execute(
            select(func.count(Lead.id)).where(func.date(Lead.created_at) == today)
        )).scalar()
        print(f"\nLeads with created_at != today: {not_today}")
        print(f"Leads with created_at == today: {is_today}")

        # Date range
        min_date = (await session.execute(select(func.min(Lead.created_at)))).scalar()
        max_date = (await session.execute(select(func.max(Lead.created_at)))).scalar()
        print(f"\nDate range: {min_date} → {max_date}")

asyncio.run(main())
