"""
הגדרת מחירים לקורסים
"""
import asyncio
from db import SessionLocal
from db.models import Course
from sqlalchemy import select

# מחירים מוצעים לפי מספר שיעורים
COURSE_PRICES = {
    "שבת": {"price": 2500.0, "payments_count": 10},      # 101 שיעורים
    "טהרה": {"price": 3500.0, "payments_count": 14},     # 44 שיעורים
    "איסור והיתר": {"price": 3000.0, "payments_count": 12},  # 41 שיעורים
}

async def set_prices():
    async with SessionLocal() as db:
        courses = (await db.execute(select(Course))).scalars().all()
        
        print("💰 מעדכן מחירים לקורסים...\n")
        
        for course in courses:
            if course.name in COURSE_PRICES:
                pricing = COURSE_PRICES[course.name]
                course.price = pricing["price"]
                course.payments_count = pricing["payments_count"]
                print(f"✅ {course.name}:")
                print(f"   מחיר: ₪{pricing['price']:,.0f}")
                print(f"   תשלומים: {pricing['payments_count']}")
                print(f"   תשלום חודשי: ₪{pricing['price']/pricing['payments_count']:,.0f}\n")
        
        await db.commit()
        print("🎉 המחירים עודכנו בהצלחה!")

if __name__ == "__main__":
    asyncio.run(set_prices())
