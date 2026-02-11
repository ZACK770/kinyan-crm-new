"""
בדיקת נקודות כניסה - האם כל הקורסים מופיעים
"""
import asyncio
from datetime import date, timedelta
from db import SessionLocal
from db.models import Course, CourseTrack, CourseModule
from sqlalchemy import select

async def verify():
    async with SessionLocal() as db:
        # קורסים עם מסלולים
        courses = (await db.execute(
            select(Course).where(Course.is_active == True)
        )).scalars().all()
        
        tracks = (await db.execute(
            select(CourseTrack).where(CourseTrack.is_active == True)
        )).scalars().all()
        
        print("🔍 בדיקת סנכרון קורסים ↔ מסלולים ↔ נקודות כניסה\n")
        print("=" * 60)
        
        for course in courses:
            if not course.name or course.name.startswith("דשג") or course.name.startswith("שדג"):
                continue  # דלג על קורסי בדיקה
            
            course_tracks = [t for t in tracks if t.course_id == course.id]
            modules = (await db.execute(
                select(CourseModule)
                .where(CourseModule.course_id == course.id)
                .order_by(CourseModule.module_order)
            )).scalars().all()
            
            print(f"\n📚 {course.name}")
            print(f"   מחיר: ₪{course.price:,.0f} ({course.payments_count} תשלומים)")
            print(f"   חוברות: {len(modules)}")
            
            if modules:
                print(f"   רשימת חוברות:")
                for m in modules:
                    print(f"     {m.module_order}. {m.name} ({m.sessions_count} שיעורים)")
            
            print(f"\n   מסלולים פעילים: {len(course_tracks)}")
            
            if course_tracks:
                for t in course_tracks:
                    status = "✅" if t.current_module_id else "⚠️"
                    print(f"     {status} {t.name}")
                    print(f"        חוברת נוכחית: {t.current_module_id or 'לא מוגדר'}")
                    print(f"        נקודת כניסה הבאה: {t.next_entry_date or 'לא מחושב'}")
            else:
                print(f"     ❌ אין מסלולים - לא יופיע בנקודות כניסה!")
        
        print("\n" + "=" * 60)
        print(f"\n📊 סיכום:")
        print(f"   קורסים פעילים: {len([c for c in courses if c.name and not c.name.startswith('דשג') and not c.name.startswith('שדג')])}")
        print(f"   מסלולים פעילים: {len(tracks)}")
        print(f"   מסלולים עם חוברת נוכחית: {len([t for t in tracks if t.current_module_id])}")

if __name__ == "__main__":
    asyncio.run(verify())
