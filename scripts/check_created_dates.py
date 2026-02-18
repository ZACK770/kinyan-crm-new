import asyncio
import sys
sys.path.insert(0, r'c:\Users\admin\kinyan-crm-new')

from db import SessionLocal
from db.models import Lead
from sqlalchemy import select, func
from datetime import datetime

async def check_dates():
    async with SessionLocal() as session:
        # ספירת לידים עם תאריך 11/2/2026
        result = await session.execute(
            select(func.count(Lead.id)).where(
                Lead.created_at >= '2026-02-11 00:00:00',
                Lead.created_at < '2026-02-12 00:00:00'
            )
        )
        count = result.scalar()
        print(f"לידים עם created_at ב-11/2/2026: {count}")
        
        # דוגמאות של לידים כאלה
        result = await session.execute(
            select(Lead.id, Lead.full_name, Lead.phone, Lead.created_at, Lead.arrival_date)
            .where(
                Lead.created_at >= '2026-02-11 00:00:00',
                Lead.created_at < '2026-02-12 00:00:00'
            )
            .limit(5)
        )
        print("\nדוגמאות:")
        for lead in result:
            print(f"  ID: {lead.id}, שם: {lead.full_name}, טלפון: {lead.phone}")
            print(f"    created_at: {lead.created_at}")
            print(f"    arrival_date: {lead.arrival_date}")

if __name__ == "__main__":
    asyncio.run(check_dates())
