"""
Debug the exact error when uploading a file via the API
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import asyncio
import io
import traceback
from sqlalchemy import text
from db import engine, SessionLocal
from db.models import File

async def debug():
    print("=" * 60)
    print("DEBUG: Checking files table schema")
    print("=" * 60)
    
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name='files' ORDER BY ordinal_position"
        ))
        for row in result:
            print(f"  {row[0]:20s} {row[1]:20s} nullable={row[2]}")
    
    print("\n" + "=" * 60)
    print("DEBUG: Trying to insert a file with file_data")
    print("=" * 60)
    
    test_data = b"Test PDF content for debug"
    
    async with SessionLocal() as db:
        try:
            db_file = File(
                filename="debug_test.pdf",
                storage_key=None,
                file_data=test_data,
                content_type="application/pdf",
                size_bytes=len(test_data),
                entity_type="temp",
                entity_id=None,
                uploaded_by=None,
                description=None,
                is_public=False,
            )
            db.add(db_file)
            await db.commit()
            await db.refresh(db_file)
            print(f"  ✅ SUCCESS! File saved with ID: {db_file.id}")
            
            # Clean up
            await db.delete(db_file)
            await db.commit()
            print(f"  ✅ Cleaned up")
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            traceback.print_exc()
            await db.rollback()
    
    print("\n" + "=" * 60)
    print("DEBUG: Trying to insert with entity_id=0 (the actual failing case)")
    print("=" * 60)
    
    async with SessionLocal() as db:
        try:
            db_file = File(
                filename="debug_test2.pdf",
                storage_key=None,
                file_data=test_data,
                content_type="application/pdf",
                size_bytes=len(test_data),
                entity_type="temp",
                entity_id=0,
                uploaded_by=None,
                description=None,
                is_public=False,
            )
            db.add(db_file)
            await db.commit()
            await db.refresh(db_file)
            print(f"  ✅ SUCCESS! File saved with ID: {db_file.id}")
            
            await db.delete(db_file)
            await db.commit()
            print(f"  ✅ Cleaned up")
            
        except Exception as e:
            print(f"  ❌ ERROR with entity_id=0: {e}")
            traceback.print_exc()
            await db.rollback()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug())
