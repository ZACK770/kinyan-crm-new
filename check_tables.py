import asyncio
from sqlalchemy import text
from db import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('sales_tasks', 'task_reports') 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print("Existing tables:", tables)
        
        # Also check the structure of sales_tasks if it exists
        if 'sales_tasks' in tables:
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'sales_tasks' 
                ORDER BY ordinal_position
            """))
            print("\nsales_tasks columns:")
            for row in result:
                print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

asyncio.run(check())
