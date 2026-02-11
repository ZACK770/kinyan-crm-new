"""
Seed data: courses, modules, salespeople, products.
Run once after DB creation: python -m db.seed
"""
import asyncio
from db import engine, SessionLocal, Base
from db.models import Course, CourseModule, Salesperson, Product


COURSES_DATA = [
    {
        "name": "שבת",
        "description": "קורס מלא בהלכות שבת - 10 מודולים",
        "semester": "א' 5786",
        "modules": [
            {"name": "בישול וחימום מאכלים", "order": 1, "sessions": 10, "hours": 16.5},
            {"name": "מלאכות השבת", "order": 2, "sessions": 13, "hours": 21.5},
            {"name": "דיני נכרי וקדושת השבת", "order": 3, "sessions": 11, "hours": 18.0},
            {"name": "הכנה משבת לחול", "order": 4, "sessions": 8, "hours": 13.0},
            {"name": "מוקצה", "order": 5, "sessions": 12, "hours": 20.0},
            {"name": "עירובין", "order": 6, "sessions": 10, "hours": 16.5},
            {"name": "בורר", "order": 7, "sessions": 9, "hours": 15.0},
            {"name": "טלטול וכתיבה", "order": 8, "sessions": 11, "hours": 18.0},
            {"name": "קידוש והבדלה", "order": 9, "sessions": 7, "hours": 11.5},
            {"name": "תפילות ומנהגי שבת", "order": 10, "sessions": 10, "hours": 16.5},
        ],
    },
    {
        "name": "איסור והיתר",
        "description": "קורס בהלכות איסור והיתר - 3 מודולים",
        "semester": "א' 5786",
        "modules": [
            {"name": "בשר בחלב", "order": 1, "sessions": 15, "hours": 25.0},
            {"name": "תערובות", "order": 2, "sessions": 14, "hours": 23.0},
            {"name": "מליחה והכשרה", "order": 3, "sessions": 12, "hours": 20.0},
        ],
    },
    {
        "name": "טהרה",
        "description": "קורס בהלכות טהרה - מודול אחד מקיף",
        "semester": "א' 5786",
        "modules": [
            {"name": "הלכות נידה וטהרה", "order": 1, "sessions": 44, "hours": 73.0},
        ],
    },
]

SALESPEOPLE_DATA = [
    {"name": "שרוליק ברים", "phone": "", "email": ""},
    {"name": "שלוימי גרוס", "phone": "", "email": ""},
    {"name": "משה גרינהויז", "phone": "", "email": ""},
    {"name": "אהרן מאירוביץ", "phone": "", "email": ""},
    {"name": "נתנאל גפנר", "phone": "", "email": ""},
]

PRODUCTS_DATA = [
    {"name": "שבת", "product_number": "1"},
    {"name": "איסור והיתר", "product_number": "2"},
    {"name": "טהרה", "product_number": "3"},
    {"name": "ממונות", "product_number": "4"},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # --- Salespeople ---
        for sp in SALESPEOPLE_DATA:
            db.add(Salesperson(**sp))
        await db.flush()
        print(f"✅ {len(SALESPEOPLE_DATA)} salespeople created")

        # --- Products ---
        for p in PRODUCTS_DATA:
            db.add(Product(**p))
        await db.flush()
        print(f"✅ {len(PRODUCTS_DATA)} products created")

        # --- Courses & Modules ---
        for cdata in COURSES_DATA:
            course = Course(
                name=cdata["name"],
                description=cdata["description"],
                semester=cdata.get("semester"),
            )
            db.add(course)
            await db.flush()  # get course.id

            for m in cdata["modules"]:
                db.add(CourseModule(
                    course_id=course.id,
                    name=m["name"],
                    module_order=m["order"],
                    sessions_count=m["sessions"],
                    hours_estimate=m["hours"],
                ))
            print(f"✅ Course '{cdata['name']}' + {len(cdata['modules'])} modules")

        await db.commit()
        print("\n🎉 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
