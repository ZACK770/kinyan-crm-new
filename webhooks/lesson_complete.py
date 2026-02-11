"""
Lesson Complete webhook handler.
Triggered when a lesson/session ends — updates session status,
optionally triggers recording upload, and notifies relevant parties.

Expected payload:
{
    "session_id": 123,           # CourseSession ID (optional if track_id + module_id provided)
    "track_id": 5,               # CourseTrack ID
    "module_id": 10,             # CourseModule ID
    "session_number": 3,         # Session number within module
    "status": "התקיים",          # מתוכנן / התקיים / בוטל
    "actual_start_time": "20:00",
    "actual_end_time": "21:30",
    "recording_url": "https://...",  # Recording URL if available
    "notes": "...",
    "source": "yemot"            # Where the trigger came from (yemot/zoom/manual)
}
"""
import logging
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import CourseSession, CourseModule, File

logger = logging.getLogger(__name__)


def parse_lesson_complete_payload(data: dict) -> dict:
    """Parse and normalize lesson completion webhook data."""
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    return {
        "session_id": data.get("session_id"),
        "track_id": data.get("track_id"),
        "module_id": data.get("module_id"),
        "session_number": data.get("session_number"),
        "status": data.get("status", "התקיים"),
        "actual_start_time": data.get("actual_start_time"),
        "actual_end_time": data.get("actual_end_time"),
        "recording_url": data.get("recording_url"),
        "notes": data.get("notes"),
        "source": data.get("source", "webhook"),
    }


async def _find_session(db: AsyncSession, parsed: dict) -> Optional[CourseSession]:
    """Find the CourseSession by ID or by track_id + module_id + session_number."""
    # Try direct session_id first
    if parsed.get("session_id"):
        stmt = select(CourseSession).where(CourseSession.id == parsed["session_id"])
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if session:
            return session
    
    # Try by track + module + session_number
    if parsed.get("track_id") and parsed.get("module_id"):
        stmt = select(CourseSession).where(
            CourseSession.track_id == parsed["track_id"],
            CourseSession.module_id == parsed["module_id"],
        )
        if parsed.get("session_number"):
            stmt = stmt.where(CourseSession.session_number == parsed["session_number"])
        
        stmt = stmt.order_by(CourseSession.session_date.desc()).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    return None


async def handle_lesson_complete_webhook(data: dict) -> dict:
    """
    Process a lesson completion webhook.
    
    Flow:
    1. Find the session
    2. Update session status and times
    3. Save recording URL if provided
    4. Return result for further processing (file upload, notifications)
    """
    parsed = parse_lesson_complete_payload(data)
    
    async for db in get_db():
        try:
            session = await _find_session(db, parsed)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found",
                    "parsed": parsed,
                }
            
            # Update session
            session.status = parsed["status"]
            
            if parsed["actual_start_time"]:
                session.actual_start_time = parsed["actual_start_time"]
            if parsed["actual_end_time"]:
                session.actual_end_time = parsed["actual_end_time"]
            if parsed["recording_url"]:
                session.recording_url = parsed["recording_url"]
            if parsed["notes"]:
                session.notes = (session.notes or "") + f"\n{parsed['notes']}" if session.notes else parsed["notes"]
            
            await db.flush()
            
            # Also update the module's recording URL if this is the latest recording
            if parsed["recording_url"]:
                module_stmt = select(CourseModule).where(CourseModule.id == session.module_id)
                module_result = await db.execute(module_stmt)
                module = module_result.scalar_one_or_none()
                if module:
                    # Update recording URL on the module level too
                    module.recording_drive_url = parsed["recording_url"]
                    await db.flush()
            
            await db.commit()
            
            result = {
                "success": True,
                "action": "session_updated",
                "session_id": session.id,
                "track_id": session.track_id,
                "module_id": session.module_id,
                "status": session.status,
                "recording_url": parsed["recording_url"],
            }
            
            logger.info(f"Lesson complete: session {session.id} → {session.status}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing lesson complete webhook: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "DB session error"}
