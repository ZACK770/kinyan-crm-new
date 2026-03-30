"""
Seed script for course tracks system
יצירת נתוני דוגמה למרצים, קורסים, מודולים ומסלולים
"""
import asyncio
from datetime import date, timedelta
from sqlalchemy import select
from db import get_async_session, Settings
from db.models import Course, CourseModule, Lecturer, CourseTrack, CourseSession


# נתוני מרצים מהטבלה שסיפקת
LECTURERS_DATA = [
    {
        "name": "מרדכי שוורץ",
        "specialty": "הלכות שבת, איסור והיתר",
        "phone": "050-1234567",
        "email": "schwartz@kinyan.org.il",
        "notes": "מרצה בכיר, מתמחה בהלכות שבת ומלאכות"
    },
    {
        "name": "יחיאל יהודה ניישטט",
        "specialty": "איסור והיתר, כשרות",
        "phone": "052-2345678",
        "email": "neishtat@kinyan.org.il",
        "notes": "מומחה בהלכות כשרות ותערובות"
    },
    {
        "name": "יוסף מרדכי סלומון",
        "specialty": "הלכות טהרה, נידה",
        "phone": "053-3456789",
        "email": "salomon@kinyan.org.il",
        "notes": "מתמחה בהלכות טהרת המשפחה"
    },
    {
        "name": "יחזקאל קרישבסקי",
        "specialty": "איסור והיתר, בשר וחלב",
        "phone": "054-4567890",
        "email": "krishevsky@kinyan.org.il",
        "notes": "מומחה בהלכות בשר בחלב ותערובות"
    },
    {
        "name": "אברהם שרגא שטיגליץ",
        "specialty": "הלכות טהרה",
        "phone": "055-5678901",
        "email": "stiglitz@kinyan.org.il",
        "notes": "מרצה מנוסה בהלכות נידה וטהרה"
    }
]


# נתוני קורסים
COURSES_DATA = [
    {
        "name": "שבת",
        "description": "מסלול מקיף בהלכות שבת - מלאכות, איסורים והיתרים",
        "is_active": True
    },
    {
        "name": "איסור והיתר",
        "description": "מסלול בהלכות כשרות - בשר בחלב, תערובות, מליחה",
        "is_active": True
    },
    {
        "name": "טהרה",
        "description": "מסלול מקיף בהלכות טהרת המשפחה",
        "is_active": True
    }
]


# מודולים לפי קורס (מהסילבוס שסיפקת)
MODULES_DATA = {
    "שבת": [
        {"name": "בישול וחימום מאכלים", "sessions_count": 10, "module_order": 1},
        {"name": "מלאכות השבת", "sessions_count": 13, "module_order": 2},
        {"name": "דיני נכרי וקדושת השבת", "sessions_count": 11, "module_order": 3},
        {"name": "מלאכות קצרות", "sessions_count": 8, "module_order": 4},
        {"name": "רפואה", "sessions_count": 7, "module_order": 5},
        {"name": "תיקון מאכלים", "sessions_count": 9, "module_order": 6},
        {"name": "מוקצה", "sessions_count": 9, "module_order": 7},
        {"name": "הוצאה ובע\"ח", "sessions_count": 11, "module_order": 8},
        {"name": "מצוות היום", "sessions_count": 12, "module_order": 9},
        {"name": "ערב וליל שבת", "sessions_count": 10, "module_order": 10}
    ],
    "איסור והיתר": [
        {"name": "בשר בחלב", "sessions_count": 13, "module_order": 1},
        {"name": "תערובות", "sessions_count": 20, "module_order": 2},
        {"name": "מליחה", "sessions_count": 10, "module_order": 3}
    ],
    "טהרה": [
        {"name": "טהרה", "sessions_count": 44, "module_order": 1}
    ]
}


# מסלולים מהטבלה שסיפקת
TRACKS_DATA = [
    {
        "course_name": "שבת",
        "lecturer_name": "מרדכי שוורץ",
        "name": "שבת - רביעי 21:00 - בני ברק - מרדכי שוורץ",
        "day_of_week": "רביעי",
        "start_time": "21:00",
        "city": "בני ברק",
        "current_module_name": "בישול וחימום מאכלים",
        "current_session_number": 1,
        "price": 2500
    },
    {
        "course_name": "איסור והיתר",
        "lecturer_name": "יחיאל יהודה ניישטט",
        "name": "איסור והיתר - שני 21:00 - בני ברק - יחיאל יהודה ניישטט",
        "day_of_week": "שני",
        "start_time": "21:00",
        "city": "בני ברק",
        "current_module_name": "תערובות",
        "current_session_number": 1,
        "price": 2200
    },
    {
        "course_name": "טהרה",
        "lecturer_name": "יוסף מרדכי סלומון",
        "name": "טהרה - ראשון 21:00 - בני ברק - יוסף מרדכי סלומון",
        "day_of_week": "ראשון",
        "start_time": "21:00",
        "city": "בני ברק",
        "current_module_name": "טהרה",
        "current_session_number": 4,
        "price": 3000
    },
    {
        "course_name": "שבת",
        "lecturer_name": "מרדכי שוורץ",
        "name": "שבת - שני 21:00 - בית שמש - מרדכי שוורץ",
        "day_of_week": "שני",
        "start_time": "21:00",
        "city": "בית שמש",
        "current_module_name": "מלאכות השבת",
        "current_session_number": 2,
        "price": 2500
    },
    {
        "course_name": "טהרה",
        "lecturer_name": "יוסף מרדכי סלומון",
        "name": "טהרה - רביעי 21:00 - בית שמש - יוסף מרדכי סלומון",
        "day_of_week": "רביעי",
        "start_time": "21:00",
        "city": "בית שמש",
        "current_module_name": "טהרה",
        "current_session_number": 39,
        "price": 3000
    },
    {
        "course_name": "שבת",
        "lecturer_name": "מרדכי שוורץ",
        "name": "שבת - שלישי 21:00 - ירושלים - מרדכי שוורץ",
        "day_of_week": "שלישי",
        "start_time": "21:00",
        "city": "ירושלים",
        "current_module_name": "דיני נכרי וקדושת השבת",
        "current_session_number": 6,
        "price": 2500
    },
    {
        "course_name": "איסור והיתר",
        "lecturer_name": "יחזקאל קרישבסקי",
        "name": "איסור והיתר - רביעי 21:00 - ירושלים - יחזקאל קרישבסקי",
        "day_of_week": "רביעי",
        "start_time": "21:00",
        "city": "ירושלים",
        "current_module_name": "תערובות",
        "current_session_number": 18,
        "price": 2200
    },
    {
        "course_name": "טהרה",
        "lecturer_name": "יוסף מרדכי סלומון",
        "name": "טהרה - שני 21:00 - ירושלים - יוסף מרדכי סלומון",
        "day_of_week": "שני",
        "start_time": "21:00",
        "city": "ירושלים",
        "current_module_name": "טהרה",
        "current_session_number": 43,
        "price": 3000
    },
    {
        "course_name": "טהרה",
        "lecturer_name": "אברהם שרגא שטיגליץ",
        "name": "טהרה - ראשון 21:00 - ביתר עילית - אברהם שרגא שטיגליץ",
        "day_of_week": "ראשון",
        "start_time": "21:00",
        "city": "ביתר עילית",
        "current_module_name": "טהרה",
        "current_session_number": 16,
        "price": 3000
    }
]


async def seed_data():
    """יצירת כל נתוני הדוגמה"""
    async with SessionLocal() as session:
        print("🌱 מתחיל seed למערכת מסלולים...\n")
        
        # 1. יצירת מרצים
        print("📚 יוצר מרצים...")
        lecturers = {}
        for lec_data in LECTURERS_DATA:
            # בדיקה אם המרצה כבר קיים
            result = await session.execute(
                select(Lecturer).where(Lecturer.name == lec_data["name"])
            )
            lecturer = result.scalar_one_or_none()
            
            if not lecturer:
                lecturer = Lecturer(**lec_data)
                session.add(lecturer)
                await session.flush()
                print(f"  ✅ נוצר: {lecturer.name}")
            else:
                print(f"  ⏭️  קיים: {lecturer.name}")
            
            lecturers[lecturer.name] = lecturer
        
        await session.commit()
        print(f"\n✅ נוצרו {len(lecturers)} מרצים\n")
        
        # 2. יצירת קורסים
        print("📖 יוצר קורסים...")
        courses = {}
        for course_data in COURSES_DATA:
            result = await session.execute(
                select(Course).where(Course.name == course_data["name"])
            )
            course = result.scalar_one_or_none()
            
            if not course:
                course = Course(**course_data)
                session.add(course)
                await session.flush()
                print(f"  ✅ נוצר: {course.name}")
            else:
                print(f"  ⏭️  קיים: {course.name}")
            
            courses[course.name] = course
        
        await session.commit()
        print(f"\n✅ נוצרו {len(courses)} קורסים\n")
        
        # 3. יצירת מודולים
        print("📑 יוצר מודולים...")
        modules = {}
        total_modules = 0
        
        for course_name, modules_list in MODULES_DATA.items():
            course = courses[course_name]
            modules[course_name] = {}
            
            for module_data in modules_list:
                result = await session.execute(
                    select(CourseModule).where(
                        CourseModule.course_id == course.id,
                        CourseModule.module_order == module_data["module_order"]
                    )
                )
                module = result.scalar_one_or_none()
                
                if not module:
                    module = CourseModule(
                        course_id=course.id,
                        name=module_data["name"],
                        sessions_count=module_data["sessions_count"],
                        module_order=module_data["module_order"]
                    )
                    session.add(module)
                    await session.flush()
                    print(f"  ✅ {course_name} - {module.name} ({module.sessions_count} מפגשים)")
                    total_modules += 1
                else:
                    print(f"  ⏭️  {course_name} - {module.name}")
                
                modules[course_name][module.name] = module
            
            await session.commit()
            print(f"\n✅ נוצרו {total_modules} מודולים\n")
            
            # 4. יצירת מסלולים
            print("🎯 יוצר מסלולים...")
            tracks = []
            
            for track_data in TRACKS_DATA:
                course = courses[track_data["course_name"]]
                lecturer = lecturers[track_data["lecturer_name"]]
                current_module = modules[track_data["course_name"]][track_data["current_module_name"]]
                
                # בדיקה אם המסלול כבר קיים
                result = await session.execute(
                    select(CourseTrack).where(
                        CourseTrack.name == track_data["name"]
                    )
                )
                track = result.scalar_one_or_none()
                
                if not track:
                    track = CourseTrack(
                        course_id=course.id,
                        lecturer_id=lecturer.id,
                        name=track_data["name"],
                        day_of_week=track_data["day_of_week"],
                        start_time=track_data["start_time"],
                        city=track_data["city"],
                        current_module_id=current_module.id,
                        current_session_number=track_data["current_session_number"],
                        price=track_data["price"],
                        is_active=True,
                        last_session_date=date.today() - timedelta(days=7)
                    )
                    session.add(track)
                    await session.flush()
                    
                    # חישוב נקודת כניסה הבאה
                    sessions_remaining = current_module.sessions_count - track.current_session_number + 1
                    if sessions_remaining > 0:
                        track.next_entry_date = track.last_session_date + timedelta(weeks=sessions_remaining)
                    
                    print(f"  ✅ {track.name}")
                    print(f"     📍 {track.city} | {track.day_of_week} {track.start_time}")
                    print(f"     📚 {current_module.name} - מפגש {track.current_session_number}")
                    if track.next_entry_date:
                        print(f"     🎯 נקודת כניסה: {track.next_entry_date.strftime('%d/%m/%Y')}")
                    tracks.append(track)
                else:
                    print(f"  ⏭️  {track_data['name']}")
            
            await session.commit()
            print(f"\n✅ נוצרו {len(tracks)} מסלולים\n")
            
            # 5. יצירת שיעורים לדוגמה (רק למסלול הראשון)
            if tracks:
                print("📅 יוצר לוח זמנים לדוגמה למסלול הראשון...")
                track = tracks[0]
                
                # קבלת כל המודולים של הקורס
                result = await session.execute(
                    select(CourseModule)
                    .where(CourseModule.course_id == track.course_id)
                    .order_by(CourseModule.module_order)
                )
                course_modules = list(result.scalars().all())
                
                # יצירת שיעורים ל-3 חודשים קדימה
                day_mapping = {
                    "ראשון": 6, "שני": 0, "שלישי": 1, "רביעי": 2,
                    "חמישי": 3, "שישי": 4, "שבת": 5
                }
                
                target_weekday = day_mapping.get(track.day_of_week, 0)
                current_date = date.today()
                days_ahead = (target_weekday - current_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                session_date = current_date + timedelta(days=days_ahead)
                
                sessions_created = 0
                for module in course_modules[:2]:  # רק 2 מודולים ראשונים
                    for session_num in range(1, min(module.sessions_count + 1, 6)):  # מקסימום 5 שיעורים למודול
                        course_session = CourseSession(
                            track_id=track.id,
                            module_id=module.id,
                            session_number=session_num,
                            session_date=session_date,
                            is_entry_point=(session_num == 1),
                            status="מתוכנן"
                        )
                        session.add(course_session)
                        session_date += timedelta(weeks=1)
                        sessions_created += 1
                
                await session.commit()
                print(f"  ✅ נוצרו {sessions_created} שיעורים לדוגמה\n")
            
            print("=" * 60)
            print("🎉 Seed הושלם בהצלחה!")
            print("=" * 60)
            print(f"📊 סיכום:")
            print(f"   • {len(lecturers)} מרצים")
            print(f"   • {len(courses)} קורסים")
            print(f"   • {total_modules} מודולים")
            print(f"   • {len(tracks)} מסלולים")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_data())
