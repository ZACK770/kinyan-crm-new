"""
Seed script - נתוני דוגמה למרצים, קורסים ומסלולים
"""
import asyncio
from datetime import date, timedelta
from sqlalchemy import select
from db import SessionLocal
from db.models import Course, CourseModule, Lecturer, CourseTrack


async def main():
    async with SessionLocal() as session:
        print("🌱 יוצר נתוני דוגמה...\n")
        
        # מרצים
        lecturers_data = [
            {"name": "מרדכי שוורץ", "specialty": "הלכות שבת", "phone": "050-1234567"},
            {"name": "יחיאל יהודה ניישטט", "specialty": "איסור והיתר", "phone": "052-2345678"},
            {"name": "יוסף מרדכי סלומון", "specialty": "הלכות טהרה", "phone": "053-3456789"},
            {"name": "יחזקאל קרישבסקי", "specialty": "כשרות", "phone": "054-4567890"},
            {"name": "אברהם שרגא שטיגליץ", "specialty": "טהרה", "phone": "055-5678901"}
        ]
        
        print("📚 יוצר מרצים...")
        lecturers = {}
        for lec in lecturers_data:
            result = await session.execute(select(Lecturer).where(Lecturer.name == lec["name"]))
            lecturer = result.scalar_one_or_none()
            if not lecturer:
                lecturer = Lecturer(**lec)
                session.add(lecturer)
                await session.flush()
                print(f"  ✅ {lecturer.name}")
            lecturers[lecturer.name] = lecturer
        
        await session.commit()
        
        # קורסים
        courses_data = [
            {"name": "שבת", "description": "הלכות שבת", "is_active": True},
            {"name": "איסור והיתר", "description": "הלכות כשרות", "is_active": True},
            {"name": "טהרה", "description": "הלכות טהרת המשפחה", "is_active": True}
        ]
        
        print("\n📖 יוצר קורסים...")
        courses = {}
        for c in courses_data:
            result = await session.execute(select(Course).where(Course.name == c["name"]))
            course = result.scalar_one_or_none()
            if not course:
                course = Course(**c)
                session.add(course)
                await session.flush()
                print(f"  ✅ {course.name}")
            courses[course.name] = course
        
        await session.commit()
        
        # מודולים לשבת
        shabbat_modules = [
            {"name": "בישול וחימום מאכלים", "sessions_count": 10, "module_order": 1},
            {"name": "מלאכות השבת", "sessions_count": 13, "module_order": 2},
            {"name": "דיני נכרי וקדושת השבת", "sessions_count": 11, "module_order": 3}
        ]
        
        print("\n📑 יוצר מודולים...")
        modules = {}
        for m in shabbat_modules:
            result = await session.execute(
                select(CourseModule).where(
                    CourseModule.course_id == courses["שבת"].id,
                    CourseModule.module_order == m["module_order"]
                )
            )
            module = result.scalar_one_or_none()
            if not module:
                module = CourseModule(course_id=courses["שבת"].id, **m)
                session.add(module)
                await session.flush()
                print(f"  ✅ {module.name}")
            modules[module.name] = module
        
        await session.commit()
        
        # מסלולים
        tracks_data = [
            {
                "course": "שבת",
                "lecturer": "מרדכי שוורץ",
                "name": "שבת - רביעי 21:00 - בני ברק",
                "day_of_week": "רביעי",
                "start_time": "21:00",
                "city": "בני ברק",
                "module": "בישול וחימום מאכלים",
                "price": 2500
            },
            {
                "course": "שבת",
                "lecturer": "מרדכי שוורץ",
                "name": "שבת - שני 21:00 - בית שמש",
                "day_of_week": "שני",
                "start_time": "21:00",
                "city": "בית שמש",
                "module": "מלאכות השבת",
                "price": 2500
            },
            {
                "course": "שבת",
                "lecturer": "מרדכי שוורץ",
                "name": "שבת - שלישי 21:00 - ירושלים",
                "day_of_week": "שלישי",
                "start_time": "21:00",
                "city": "ירושלים",
                "module": "דיני נכרי וקדושת השבת",
                "price": 2500
            }
        ]
        
        print("\n🎯 יוצר מסלולים...")
        for t in tracks_data:
            result = await session.execute(
                select(CourseTrack).where(CourseTrack.name == t["name"])
            )
            track = result.scalar_one_or_none()
            if not track:
                track = CourseTrack(
                    course_id=courses[t["course"]].id,
                    lecturer_id=lecturers[t["lecturer"]].id,
                    name=t["name"],
                    day_of_week=t["day_of_week"],
                    start_time=t["start_time"],
                    city=t["city"],
                    current_module_id=modules[t["module"]].id,
                    current_session_number=1,
                    price=t["price"],
                    is_active=True,
                    last_session_date=date.today() - timedelta(days=7),
                    next_entry_date=date.today() + timedelta(days=14)
                )
                session.add(track)
                await session.flush()
                print(f"  ✅ {track.name}")
        
        await session.commit()
        
        print("\n" + "="*60)
        print("🎉 הושלם בהצלחה!")
        print(f"   • {len(lecturers)} מרצים")
        print(f"   • {len(courses)} קורסים")
        print(f"   • {len(modules)} מודולים")
        print(f"   • {len(tracks_data)} מסלולים")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
