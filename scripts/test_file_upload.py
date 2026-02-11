"""
Test file upload to debug the issue
"""
import sys
import io
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db, engine
from db.models import File
from services.storage import storage_service

async def test_upload():
    print("=" * 60)
    print("Testing file upload with entity_id=0")
    print("=" * 60)
    
    # Create a test file
    test_content = b"Test PDF content"
    test_file = io.BytesIO(test_content)
    
    # Test storage service
    print("\n1. Testing storage_service.upload_file()...")
    result = await storage_service.upload_file(
        file_data=test_file,
        filename="test.pdf",
        folder="temp/0",
        content_type="application/pdf"
    )
    print(f"   Result: {result}")
    
    # Test the logic for entity_id
    print("\n2. Testing entity_id logic...")
    entity_type = "temp"
    entity_id = 0
    
    # This is what the API does:
    final_entity_type = entity_type if entity_type else None
    final_entity_id = entity_id if entity_id and entity_id > 0 else None
    
    print(f"   Input: entity_type={entity_type!r}, entity_id={entity_id!r}")
    print(f"   Output: entity_type={final_entity_type!r}, entity_id={final_entity_id!r}")
    
    # Test creating File object
    print("\n3. Testing File object creation...")
    db_file = File(
        filename="test.pdf",
        storage_key=result.get('key'),
        file_data=result.get('data'),
        content_type=result.get('content_type'),
        size_bytes=result.get('size'),
        entity_type=final_entity_type,
        entity_id=final_entity_id,
        uploaded_by=None,
        description=None,
        is_public=False,
    )
    print(f"   File object created:")
    print(f"   - filename: {db_file.filename}")
    print(f"   - storage_key: {db_file.storage_key}")
    print(f"   - entity_type: {db_file.entity_type}")
    print(f"   - entity_id: {db_file.entity_id}")
    print(f"   - file_data size: {len(db_file.file_data) if db_file.file_data else 0} bytes")
    
    # Test saving to DB
    print("\n4. Testing database save...")
    async for db in get_db():
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
        print(f"   ✅ Saved to DB with ID: {db_file.id}")
        
        # Clean up
        await db.delete(db_file)
        await db.commit()
        print(f"   ✅ Cleaned up test file")
        break
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_upload())
