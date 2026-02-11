import asyncio
import sys
sys.path.insert(0, r'c:\Users\admin\kinyan-crm-new')

from db import SessionLocal
from db.models import Lead
from sqlalchemy import select, func

async def main():
    async with SessionLocal() as session:
        # ספירת לידים
        count_result = await session.execute(select(func.count(Lead.id)))
        total = count_result.scalar()
        
        # ספירת לידים מייבוא
        import_result = await session.execute(
            select(func.count(Lead.id)).where(Lead.created_by == "import_script")
        )
        imported = import_result.scalar()
        
        print(f"סה\"כ לידים במערכת: {total}")
        print(f"לידים מייבוא: {imported}")
        print(f"לידים אחרים: {total - imported}")

if __name__ == "__main__":
    asyncio.run(main())
