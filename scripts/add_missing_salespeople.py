"""Add missing salespeople to DB (inactive — no user account needed)"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MISSING_SALESPEOPLE = [
    "אברימי ברים",
    "דודי וצלר",
    "חיים ברים",
    "מוטי דבלינגר",
    "מוטי העכט",
    "מרדכי ארנפלד",
    "נפתלי לרנר",
]

async def main():
    from db import SessionLocal
    from db.models import Salesperson
    from sqlalchemy import select

    async with SessionLocal() as session:
        for name in MISSING_SALESPEOPLE:
            # Check if already exists
            result = await session.execute(select(Salesperson).where(Salesperson.name == name))
            if result.scalar_one_or_none():
                print(f"  ⏭️  {name} — already exists")
                continue
            sp = Salesperson(name=name, is_active=False)
            session.add(sp)
            await session.flush()
            print(f"  ✅ Created: {name} (ID {sp.id})")

        await session.commit()
        print("\nDone!")

asyncio.run(main())
