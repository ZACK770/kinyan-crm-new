#!/usr/bin/env python3
import asyncio
import asyncpg
import os

async def main():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        print("Tables in database:")
        for t in tables:
            print(f"  {t['tablename']}")
            
        # Check specifically for exam_dates
        exam_dates_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'exam_dates')"
        )
        print(f"\nexam_dates table exists: {exam_dates_exists}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
