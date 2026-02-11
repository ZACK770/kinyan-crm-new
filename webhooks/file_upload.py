"""
File Upload webhook handler.
Triggered when a file needs to be associated with an entity automatically.
Typically used when a lesson recording is ready and needs to be linked.

Expected payload:
{
    "entity_type": "sessions",       # sessions/modules/leads/students
    "entity_id": 123,                # Entity ID
    "file_url": "https://...",       # URL of the file to register
    "filename": "recording_2026.mp4",
    "content_type": "video/mp4",
    "size_bytes": 1234567,
    "description": "הקלטת שיעור 3",
    "source": "yemot",              # Where the file came from
    "session_id": 456,              # Optional: link to specific session
    "module_id": 789,               # Optional: link to specific module
}
"""
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import File, CourseSession, CourseModule

logger = logging.getLogger(__name__)


def parse_file_upload_payload(data: dict) -> dict:
    """Parse and normalize file upload webhook data."""
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    return {
        "entity_type": data.get("entity_type", "sessions"),
        "entity_id": data.get("entity_id"),
        "file_url": data.get("file_url", data.get("url", "")),
        "filename": data.get("filename", "recording"),
        "content_type": data.get("content_type", "application/octet-stream"),
        "size_bytes": data.get("size_bytes"),
        "description": data.get("description", ""),
        "source": data.get("source", "webhook"),
        "session_id": data.get("session_id"),
        "module_id": data.get("module_id"),
    }


async def handle_file_upload_webhook(data: dict) -> dict:
    """
    Process a file upload webhook.
    
    Flow:
    1. Parse payload
    2. Create File record in DB (linked to entity)
    3. If session_id provided, update session recording_url
    4. If module_id provided, update module recording URLs
    """
    parsed = parse_file_upload_payload(data)
    
    if not parsed["file_url"]:
        return {"success": False, "error": "Missing file_url"}
    
    async for db in get_db():
        try:
            # Create File record
            db_file = File(
                filename=parsed["filename"],
                storage_key=parsed["file_url"],  # For external URLs, store as storage_key
                content_type=parsed["content_type"],
                size_bytes=parsed["size_bytes"],
                entity_type=parsed["entity_type"],
                entity_id=parsed["entity_id"],
                description=parsed["description"] or f"Auto-uploaded from {parsed['source']}",
                is_public=False,
            )
            db.add(db_file)
            await db.flush()
            
            result = {
                "success": True,
                "action": "file_registered",
                "file_id": db_file.id,
                "filename": db_file.filename,
            }
            
            # Update session recording URL if session_id provided
            if parsed["session_id"]:
                stmt = select(CourseSession).where(CourseSession.id == parsed["session_id"])
                session_result = await db.execute(stmt)
                session = session_result.scalar_one_or_none()
                if session:
                    session.recording_url = parsed["file_url"]
                    await db.flush()
                    result["session_id"] = session.id
                    result["session_updated"] = True
            
            # Update module recording URL if module_id provided
            if parsed["module_id"]:
                stmt = select(CourseModule).where(CourseModule.id == parsed["module_id"])
                module_result = await db.execute(stmt)
                module = module_result.scalar_one_or_none()
                if module:
                    module.recording_drive_url = parsed["file_url"]
                    await db.flush()
                    result["module_id"] = module.id
                    result["module_updated"] = True
            
            await db.commit()
            
            logger.info(f"File registered: {db_file.filename} → {parsed['entity_type']}/{parsed['entity_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing file upload webhook: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "DB session error"}
