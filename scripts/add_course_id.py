"""Add course_id column to leads table if missing."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from db import engine

async def add_column():
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'leads' AND column_name = 'course_id'"
        ))
        exists = result.scalar() is not None
        
        if not exists:
            await conn.execute(text(
                'ALTER TABLE leads ADD COLUMN course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL'
            ))
            await conn.execute(text('CREATE INDEX IF NOT EXISTS idx_leads_course ON leads(course_id)'))
            print('Column course_id added to leads')
        else:
            print('Column course_id already exists')

if __name__ == "__main__":
    asyncio.run(add_column())
