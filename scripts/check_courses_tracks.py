"""
בדיקת מצב קורסים, מסלולים ונקודות כניסה
"""
import asyncio
from db import SessionLocal
from db.models import Course, CourseTrack, CourseModule
from sqlalchemy import select

async def check():
    async with SessionLocal() as db:
        # קורסים
        courses = (await db.execute(select(Course))).scalars().all()
        print(f'📚 קורסים: {len(courses)}')
        for c in courses:
            print(f'  - {c.name} (ID: {c.id}, מחיר: {c.price}, תשלומים: {c.payments_count})')
        
        # מסלולים
        tracks = (await db.execute(select(CourseTrack))).scalars().all()
        print(f'\n🛤️  מסלולים: {len(tracks)}')
        for t in tracks:
            course_name = next((c.name for c in courses if c.id == t.course_id), 'לא ידוע')
            print(f'  - {t.name}')
            print(f'    קורס: {course_name} (ID: {t.course_id})')
            print(f'    מחיר: {t.price if t.price else "לא מוגדר"}')
            print(f'    פעיל: {t.is_active}')
        
        # חוברות
        modules = (await db.execute(select(CourseModule))).scalars().all()
        print(f'\n📖 חוברות: {len(modules)}')
        for course in courses:
            course_modules = [m for m in modules if m.course_id == course.id]
            print(f'  {course.name}: {len(course_modules)} חוברות')

if __name__ == "__main__":
    asyncio.run(check())
