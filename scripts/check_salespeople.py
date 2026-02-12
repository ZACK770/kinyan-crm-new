"""Check which salespeople exist in DB vs what the Excel needs"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.import_api import SALESPERSON_MAPPING

async def main():
    from db import SessionLocal
    from db.models import Salesperson
    from sqlalchemy import select

    needed = set(v for v in SALESPERSON_MAPPING.values() if v is not None)

    async with SessionLocal() as session:
        result = await session.execute(select(Salesperson.id, Salesperson.name))
        existing = {row.name: row.id for row in result}

    print("=== Salespeople in DB ===")
    for name, sid in sorted(existing.items(), key=lambda x: x[1]):
        print(f"  [{sid}] {name}")

    print(f"\n=== Needed by import ({len(needed)}) ===")
    missing = []
    for name in sorted(needed):
        if name in existing:
            print(f"  ✅ {name} (ID {existing[name]})")
        else:
            print(f"  ❌ {name} — MISSING")
            missing.append(name)

    if missing:
        print(f"\n⚠️  {len(missing)} salespeople need to be created:")
        for name in missing:
            print(f"    - {name}")
    else:
        print("\n✅ All salespeople exist in DB!")

asyncio.run(main())
