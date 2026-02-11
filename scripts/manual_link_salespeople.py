"""
סקריפט לשיוך ידני של salespeople למשתמשים לפי שם
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from db import SessionLocal
from db.models import Salesperson, User


# מיפוי ידני לפי שם
MANUAL_MAPPING = {
    "ישראל ברים": "s0527635459@gmail.com",
    "שלמה גרוס": "sh0533185546@gmail.com",
    "אהרן מאירוביץ": "a0533170532@gmail.com",
    "משה גרינהויז": "MG0583297410@GMAIL.COM",
}


async def main():
    async with SessionLocal() as db:
        print("=== שיוך salespeople למשתמשים ===\n")
        
        updated = 0
        
        for sp_name, user_email in MANUAL_MAPPING.items():
            # מצא salesperson
            sp_result = await db.execute(
                select(Salesperson).where(Salesperson.name == sp_name)
            )
            sp = sp_result.scalar_one_or_none()
            
            if not sp:
                print(f"⚠️  לא נמצא salesperson: {sp_name}")
                continue
            
            # מצא משתמש
            user_result = await db.execute(
                select(User).where(User.email == user_email)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                print(f"⚠️  לא נמצא משתמש: {user_email}")
                continue
            
            # שיוך
            sp.user_id = user.id
            
            # עדכון רמת הרשאה ל-salesperson אם נמוך מזה
            if user.permission_level < 25:
                user.role_name = "salesperson"
                user.permission_level = 25
                print(f"✓ {sp_name} → {user.full_name} (עודכן ל-salesperson)")
            else:
                print(f"✓ {sp_name} → {user.full_name} (נשאר {user.role_name})")
            
            updated += 1
        
        await db.commit()
        
        print(f"\n=== סיכום ===")
        print(f"שויכו {updated} salespeople למשתמשים")
        
        # הצגת מצב סופי
        print("\n=== מצב סופי ===")
        result = await db.execute(
            select(Salesperson, User)
            .outerjoin(User, Salesperson.user_id == User.id)
            .order_by(Salesperson.id)
        )
        final = result.all()
        
        for sp, user in final:
            if user:
                print(f"  ✓ {sp.name} → {user.full_name} ({user.role_name}, level {user.permission_level})")
            else:
                print(f"  ✗ {sp.name} - לא משויך למשתמש")


if __name__ == "__main__":
    asyncio.run(main())
