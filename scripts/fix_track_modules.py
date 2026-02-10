"""
תיקון חוברות נוכחיות במסלולים - הצבת החוברת הראשונה הנכונה
"""
import asyncio
from db import SessionLocal
from db.models import CourseTrack, CourseModule
from sqlalchemy import select

async def fix_modules():
    async with SessionLocal() as db:
        tracks = (await db.execute(select(CourseTrack))).scalars().all()
        
        print("🔧 מתקן חוברות נוכחיות במסלולים...\n")
        
        for track in tracks:
            # מצא חוברת ראשונה של הקורס
            first_module = (await db.execute(
                select(CourseModule)
                .where(CourseModule.course_id == track.course_id)
                .order_by(CourseModule.module_order)
            )).scalars().first()
            
            if first_module:
                old_module_id = track.current_module_id
                track.current_module_id = first_module.id
                track.current_session_number = 1
                
                print(f"✅ {track.name}")
                print(f"   חוברת ישנה: {old_module_id} → חוברת חדשה: {first_module.id} ({first_module.name})")
            else:
                print(f"⚠️  {track.name} - אין חוברות לקורס")
        
        await db.commit()
        print("\n🎉 החוברות תוקנו!")

if __name__ == "__main__":
    asyncio.run(fix_modules())
