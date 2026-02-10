"""
בדיקת IDs של חוברות
"""
import asyncio
from db import SessionLocal
from db.models import Course, CourseModule
from sqlalchemy import select

async def check():
    async with SessionLocal() as db:
        modules = (await db.execute(
            select(CourseModule).order_by(CourseModule.id)
        )).scalars().all()
        
        courses = (await db.execute(select(Course))).scalars().all()
        courses_dict = {c.id: c.name for c in courses}
        
        print("📖 כל החוברות במערכת:\n")
        for m in modules:
            course_name = courses_dict.get(m.course_id, "לא ידוע")
            print(f"ID: {m.id} | קורס: {course_name} (ID: {m.course_id}) | {m.module_order}. {m.name}")

if __name__ == "__main__":
    asyncio.run(check())
