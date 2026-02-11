"""
Simulate the EXACT upload flow from the API to find the real error
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import asyncio
import io
import traceback
from db import SessionLocal
from db.models import File
from services.storage import storage_service

async def simulate_upload():
    print("=" * 60)
    print("Simulating EXACT API upload flow")
    print(f"Storage backend: {storage_service.backend}")
    print("=" * 60)
    
    # Simulate a real PDF upload (92KB like in the error log)
    test_data = b"X" * 92657  # Same size as in error log
    file_obj = io.BytesIO(test_data)
    
    # Step 1: storage_service.upload_file (same as API)
    print("\n1. Calling storage_service.upload_file()...")
    try:
        result = await storage_service.upload_file(
            file_data=file_obj,
            filename="test.pdf",
            folder="temp/0",
            content_type="application/pdf"
        )
        print(f"   Result keys: {list(result.keys())}")
        print(f"   key={result.get('key')}")
        print(f"   size={result.get('size')}")
        print(f"   data length={len(result.get('data', b''))}")
    except Exception as e:
        print(f"   ❌ ERROR in upload_file: {e}")
        traceback.print_exc()
        return

    # Step 2: Create File object (same as API)
    print("\n2. Creating File object...")
    entity_type = "temp"
    entity_id = 0
    final_entity_id = entity_id if entity_id and entity_id > 0 else None
    
    db_file = File(
        filename="test.pdf",
        storage_key=result.get('key'),
        file_data=result.get('data'),
        content_type=result.get('content_type'),
        size_bytes=result.get('size'),
        entity_type=entity_type if entity_type else None,
        entity_id=final_entity_id,
        uploaded_by=0,  # user.id in DEV mode
        description=None,
        is_public=False,
    )
    print(f"   filename={db_file.filename}")
    print(f"   storage_key={db_file.storage_key}")
    print(f"   entity_type={db_file.entity_type}")
    print(f"   entity_id={db_file.entity_id}")
    print(f"   uploaded_by={db_file.uploaded_by}")
    print(f"   file_data size={len(db_file.file_data) if db_file.file_data else 0}")

    # Step 3: Save to DB (same as API)
    print("\n3. Saving to DB...")
    async with SessionLocal() as db:
        try:
            db.add(db_file)
            await db.commit()
            await db.refresh(db_file)
            print(f"   ✅ SUCCESS! ID={db_file.id}")
            
            # Clean up
            await db.delete(db_file)
            await db.commit()
            print(f"   ✅ Cleaned up")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(simulate_upload())
