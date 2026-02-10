"""
הוספת חוברות חסרות לקורסי טהרה ואיסור והיתר
"""
import asyncio
from db import SessionLocal
from db.models import Course, CourseModule
from sqlalchemy import select

# נתוני חוברות לפי seed.py
TAHARA_MODULES = [
    {"name": "הלכות נידה וטהרה", "order": 1, "sessions": 44, "hours": 73.0},
]

ISSUR_VEHETER_MODULES = [
    {"name": "בשר בחלב", "order": 1, "sessions": 15, "hours": 25.0},
    {"name": "תערובות", "order": 2, "sessions": 14, "hours": 23.0},
    {"name": "מליחה והכשרה", "order": 3, "sessions": 12, "hours": 20.0},
]

async def add_modules():
    async with SessionLocal() as db:
        # מצא קורסים
        courses = (await db.execute(select(Course))).scalars().all()
        
        tahara_course = next((c for c in courses if c.name == "טהרה"), None)
        issur_course = next((c for c in courses if c.name == "איסור והיתר"), None)
        
        if not tahara_course:
            print("❌ קורס טהרה לא נמצא")
            return
        
        if not issur_course:
            print("❌ קורס איסור והיתר לא נמצא")
            return
        
        # בדוק אם כבר יש חוברות
        existing_modules = (await db.execute(
            select(CourseModule).where(
                CourseModule.course_id.in_([tahara_course.id, issur_course.id])
            )
        )).scalars().all()
        
        if existing_modules:
            print(f"⚠️  כבר קיימות {len(existing_modules)} חוברות. מוחק...")
            for m in existing_modules:
                await db.delete(m)
            await db.flush()
        
        # הוסף חוברות לטהרה
        print(f"\n📖 מוסיף חוברות לקורס טהרה (ID: {tahara_course.id})...")
        for m_data in TAHARA_MODULES:
            module = CourseModule(
                course_id=tahara_course.id,
                name=m_data["name"],
                module_order=m_data["order"],
                sessions_count=m_data["sessions"],
                hours_estimate=m_data["hours"],
            )
            db.add(module)
            print(f"  ✅ {m_data['name']} ({m_data['sessions']} שיעורים)")
        
        # הוסף חוברות לאיסור והיתר
        print(f"\n📖 מוסיף חוברות לקורס איסור והיתר (ID: {issur_course.id})...")
        for m_data in ISSUR_VEHETER_MODULES:
            module = CourseModule(
                course_id=issur_course.id,
                name=m_data["name"],
                module_order=m_data["order"],
                sessions_count=m_data["sessions"],
                hours_estimate=m_data["hours"],
            )
            db.add(module)
            print(f"  ✅ {m_data['name']} ({m_data['sessions']} שיעורים)")
        
        await db.commit()
        print("\n🎉 החוברות נוספו בהצלחה!")
        
        # עדכן total_sessions בקורסים
        print("\n🔄 מעדכן total_sessions בקורסים...")
        tahara_course.total_sessions = sum(m["sessions"] for m in TAHARA_MODULES)
        issur_course.total_sessions = sum(m["sessions"] for m in ISSUR_VEHETER_MODULES)
        await db.commit()
        print(f"  ✅ טהרה: {tahara_course.total_sessions} שיעורים")
        print(f"  ✅ איסור והיתר: {issur_course.total_sessions} שיעורים")

if __name__ == "__main__":
    asyncio.run(add_modules())
