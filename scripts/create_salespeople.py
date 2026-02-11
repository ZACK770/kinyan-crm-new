import asyncio
import sys
sys.path.insert(0, r'c:\Users\admin\kinyan-crm-new')

from db import SessionLocal
from db.models import Salesperson
from sqlalchemy import select

async def main():
    salespeople_to_create = [
        {"name": "ישראל ברים", "notes": "שרוליק - 58 לידים מהמערכת הישנה"},
        {"name": "שלמה גרוס", "notes": "שלוימי גרוס - 33 לידים מהמערכת הישנה"},
        {"name": "אהרן מאירוביץ", "notes": "51 לידים מהמערכת הישנה"},
        {"name": "משה גרינהויז", "notes": "54 לידים מהמערכת הישנה"},
        {"name": "נתנאל גפנר", "notes": "2 לידים מהמערכת הישנה"},
        {"name": "שלמה דנציגר", "notes": "1 ליד מהמערכת הישנה"},
    ]
    
    async with SessionLocal() as session:
        print("=" * 80)
        print("יצירת אנשי מכירות")
        print("=" * 80)
        
        for sp_data in salespeople_to_create:
            # בדיקה אם כבר קיים
            result = await session.execute(
                select(Salesperson).where(Salesperson.name == sp_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"✓ {sp_data['name']} כבר קיים (ID: {existing.id})")
            else:
                new_sp = Salesperson(
                    name=sp_data["name"],
                    notes=sp_data["notes"],
                    is_active=True
                )
                session.add(new_sp)
                await session.flush()
                print(f"✓ נוצר: {sp_data['name']} (ID: {new_sp.id})")
        
        await session.commit()
        print("\n" + "=" * 80)
        print("סיום - כל אנשי המכירות נוצרו בהצלחה")
        print("=" * 80)
        
        # הצגת רשימה מעודכנת
        result = await session.execute(select(Salesperson))
        all_salespeople = result.scalars().all()
        print("\nרשימת אנשי מכירות במערכת:")
        for sp in all_salespeople:
            print(f"  ID: {sp.id}, שם: {sp.name}")

if __name__ == "__main__":
    asyncio.run(main())
