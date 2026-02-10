"""
יצירת מסלולים לקורסי טהרה ואיסור והיתר
"""
import asyncio
from db import SessionLocal
from db.models import Course, CourseTrack, Lecturer, CourseModule
from sqlalchemy import select

# מסלולים מוצעים
TRACKS_DATA = [
    {
        "course_name": "טהרה",
        "lecturer_name": "הרב יעקב כהן",  # נצטרך ליצור מרצה אם לא קיים
        "name": "טהרה - רביעי 20:30 - ירושלים",
        "day_of_week": "רביעי",
        "start_time": "20:30",
        "city": "ירושלים",
    },
    {
        "course_name": "טהרה",
        "lecturer_name": "הרב יעקב כהן",
        "name": "טהרה - שני 21:00 - בני ברק",
        "day_of_week": "שני",
        "start_time": "21:00",
        "city": "בני ברק",
    },
    {
        "course_name": "איסור והיתר",
        "lecturer_name": "הרב משה לוי",
        "name": "איסור והיתר - שלישי 20:30 - ירושלים",
        "day_of_week": "שלישי",
        "start_time": "20:30",
        "city": "ירושלים",
    },
    {
        "course_name": "איסור והיתר",
        "lecturer_name": "הרב משה לוי",
        "name": "איסור והיתר - רביעי 21:00 - בית שמש",
        "day_of_week": "רביעי",
        "start_time": "21:00",
        "city": "בית שמש",
    },
]

async def create_tracks():
    async with SessionLocal() as db:
        # טען קורסים
        courses = (await db.execute(select(Course))).scalars().all()
        courses_dict = {c.name: c for c in courses}
        
        # טען מרצים
        lecturers = (await db.execute(select(Lecturer))).scalars().all()
        lecturers_dict = {l.name: l for l in lecturers}
        
        # צור מרצים חסרים
        for track_data in TRACKS_DATA:
            lecturer_name = track_data["lecturer_name"]
            if lecturer_name not in lecturers_dict:
                print(f"📝 יוצר מרצה חדש: {lecturer_name}")
                lecturer = Lecturer(name=lecturer_name)
                db.add(lecturer)
                await db.flush()
                lecturers_dict[lecturer_name] = lecturer
        
        await db.commit()
        
        # צור מסלולים
        print("\n🛤️  יוצר מסלולים...\n")
        
        for track_data in TRACKS_DATA:
            course = courses_dict.get(track_data["course_name"])
            lecturer = lecturers_dict.get(track_data["lecturer_name"])
            
            if not course:
                print(f"❌ קורס {track_data['course_name']} לא נמצא")
                continue
            
            if not lecturer:
                print(f"❌ מרצה {track_data['lecturer_name']} לא נמצא")
                continue
            
            # מצא חוברת ראשונה
            first_module = (await db.execute(
                select(CourseModule)
                .where(CourseModule.course_id == course.id)
                .order_by(CourseModule.module_order)
            )).scalars().first()
            
            if not first_module:
                print(f"❌ אין חוברות לקורס {course.name}")
                continue
            
            # צור מסלול
            track = CourseTrack(
                course_id=course.id,
                lecturer_id=lecturer.id,
                name=track_data["name"],
                day_of_week=track_data["day_of_week"],
                start_time=track_data["start_time"],
                city=track_data["city"],
                price=course.price,  # מחיר מהקורס
                current_module_id=first_module.id,
                current_session_number=1,
                is_active=True,
            )
            db.add(track)
            
            print(f"✅ {track_data['name']}")
            print(f"   קורס: {course.name}")
            print(f"   מרצה: {lecturer.name}")
            print(f"   מחיר: ₪{course.price:,.0f}")
            print(f"   חוברת ראשונה: {first_module.name}\n")
        
        await db.commit()
        print("🎉 המסלולים נוצרו בהצלחה!")

if __name__ == "__main__":
    asyncio.run(create_tracks())
