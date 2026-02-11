"""
סקריפט לשיוך salespeople קיימים למשתמשי מערכת
ועדכון משתמשים לרמת salesperson
"""
import asyncio
import sys
from pathlib import Path

# הוספת הנתיב לסביבה
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from db import SessionLocal
from db.models import Salesperson, User


async def main():
    async with SessionLocal() as db:
        # שלב 1: הצגת salespeople קיימים
        print("=== Salespeople קיימים ===")
        result = await db.execute(
            select(Salesperson.id, Salesperson.name, Salesperson.email, Salesperson.user_id)
            .order_by(Salesperson.id)
        )
        salespeople = result.all()
        
        if not salespeople:
            print("לא נמצאו salespeople במערכת")
            return
        
        for sp in salespeople:
            status = f"משויך ל-user_id={sp.user_id}" if sp.user_id else "לא משויך"
            print(f"  {sp.id}: {sp.name} ({sp.email}) - {status}")
        
        # שלב 2: הצגת משתמשים קיימים
        print("\n=== משתמשים קיימים ===")
        result = await db.execute(
            select(User.id, User.full_name, User.email, User.role_name, User.permission_level)
            .order_by(User.id)
        )
        users = result.all()
        
        for u in users:
            print(f"  {u.id}: {u.full_name} ({u.email}) - {u.role_name} (level {u.permission_level})")
        
        # שלב 3: שיוך אוטומטי לפי email
        print("\n=== שיוך אוטומטי לפי email ===")
        matched = 0
        for sp in salespeople:
            if sp.user_id:
                continue  # כבר משויך
            
            if not sp.email:
                print(f"  ⚠️  {sp.name} - אין email, דילוג")
                continue
            
            # חיפוש משתמש לפי email
            result = await db.execute(
                select(User).where(User.email == sp.email)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # שיוך salesperson למשתמש
                await db.execute(
                    update(Salesperson)
                    .where(Salesperson.id == sp.id)
                    .values(user_id=user.id)
                )
                
                # עדכון משתמש לרמת salesperson אם הוא editor או נמוך יותר
                if user.permission_level < 25:
                    await db.execute(
                        update(User)
                        .where(User.id == user.id)
                        .values(role_name="salesperson", permission_level=25)
                    )
                    print(f"  ✓ {sp.name} → {user.full_name} (עודכן ל-salesperson)")
                else:
                    print(f"  ✓ {sp.name} → {user.full_name} (נשאר {user.role_name})")
                
                matched += 1
            else:
                print(f"  ⚠️  {sp.name} ({sp.email}) - לא נמצא משתמש תואם")
        
        await db.commit()
        
        print(f"\n=== סיכום ===")
        print(f"שויכו {matched} salespeople למשתמשים")
        
        # שלב 4: הצגת מצב סופי
        print("\n=== מצב סופי ===")
        result = await db.execute(
            select(Salesperson, User)
            .outerjoin(User, Salesperson.user_id == User.id)
            .order_by(Salesperson.id)
        )
        final = result.all()
        
        for sp, user in final:
            if user:
                print(f"  ✓ {sp.name} → {user.full_name} ({user.role_name})")
            else:
                print(f"  ✗ {sp.name} - לא משויך למשתמש")


if __name__ == "__main__":
    asyncio.run(main())
