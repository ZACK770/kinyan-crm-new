"""Add missing columns to database tables."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from db import engine

async def add_columns():
    async with engine.begin() as conn:
        # Add course_id to leads if missing
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'leads' AND column_name = 'course_id'"
        ))
        if not result.scalar():
            await conn.execute(text(
                'ALTER TABLE leads ADD COLUMN course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL'
            ))
            await conn.execute(text('CREATE INDEX IF NOT EXISTS idx_leads_course ON leads(course_id)'))
            print('Added course_id to leads')
        else:
            print('course_id already exists in leads')
        
        # Add nedarim_payer_id to students if missing
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'students' AND column_name = 'nedarim_payer_id'"
        ))
        if not result.scalar():
            await conn.execute(text('ALTER TABLE students ADD COLUMN nedarim_payer_id VARCHAR(50)'))
            print('Added nedarim_payer_id to students')
        else:
            print('nedarim_payer_id already exists in students')

if __name__ == "__main__":
    asyncio.run(add_columns())
