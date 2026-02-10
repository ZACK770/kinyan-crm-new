"""Check PostgreSQL database tables and schema"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from db import engine

async def check_tables():
    async with engine.begin() as conn:
        # Get all tables
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        
        print(f"Total tables: {len(tables)}\n")
        print("Tables in database:")
        for table in tables:
            print(f"  - {table}")
        
        # Check for foreign key constraints between leads and students
        print("\n\nForeign keys in 'leads' table:")
        result = await conn.execute(text("""
            SELECT 
                tc.constraint_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name='leads'
            ORDER BY tc.constraint_name
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]} -> {row[2]}.{row[3]}")
        
        print("\n\nForeign keys in 'students' table:")
        result = await conn.execute(text("""
            SELECT 
                tc.constraint_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name='students'
            ORDER BY tc.constraint_name
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]} -> {row[2]}.{row[3]}")

if __name__ == "__main__":
    asyncio.run(check_tables())
