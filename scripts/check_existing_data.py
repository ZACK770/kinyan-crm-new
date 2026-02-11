import asyncio
import sys
sys.path.insert(0, r'c:\Users\admin\kinyan-crm-new')

from db import SessionLocal
from db.models import Course, Salesperson
from sqlalchemy import select

async def main():
    async with SessionLocal() as session:
        # בדיקת קורסים
        courses_result = await session.execute(select(Course))
        courses = courses_result.scalars().all()
        
        print("=" * 80)
        print("קורסים קיימים במערכת:")
        print("=" * 80)
        if courses:
            for c in courses:
                print(f"ID: {c.id}, שם: {c.name}, פעיל: {c.is_active}")
        else:
            print("אין קורסים במערכת")
        
        # בדיקת אנשי מכירות
        salespeople_result = await session.execute(select(Salesperson))
        salespeople = salespeople_result.scalars().all()
        
        print("\n" + "=" * 80)
        print("אנשי מכירות קיימים במערכת:")
        print("=" * 80)
        if salespeople:
            for s in salespeople:
                print(f"ID: {s.id}, שם: {s.name}, פעיל: {s.is_active}")
        else:
            print("אין אנשי מכירות במערכת")

if __name__ == "__main__":
    asyncio.run(main())
