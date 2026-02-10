"""
Course Tracks API - endpoints לניהול מסלולי לימוד
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db import get_db
from services import course_tracks, course_sessions
from api.dependencies import get_current_user, require_permission


router = APIRouter(prefix="/api/course-tracks", tags=["Course Tracks"])


# ============================================================
# Pydantic Models
# ============================================================

class CourseTrackCreate(BaseModel):
    course_id: int
    lecturer_id: int
    name: str
    day_of_week: str = Field(..., description="יום השבוע: ראשון/שני/שלישי/רביעי/חמישי/שישי")
    start_time: str = Field(..., description="שעת התחלה בפורמט HH:MM")
    city: str
    zoom_url: Optional[str] = None
    price: Optional[float] = None
    current_module_id: Optional[int] = None


class CourseTrackUpdate(BaseModel):
    name: Optional[str] = None
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    city: Optional[str] = None
    zoom_url: Optional[str] = None
    price: Optional[float] = None
    current_module_id: Optional[int] = None
    current_session_number: Optional[int] = None
    is_active: Optional[bool] = None


class CourseTrackResponse(BaseModel):
    id: int
    course_id: int
    lecturer_id: int
    name: str
    day_of_week: str
    start_time: str
    city: str
    zoom_url: Optional[str]
    price: Optional[float]
    current_module_id: Optional[int]
    current_session_number: int
    last_session_date: Optional[date]
    next_entry_date: Optional[date]
    is_active: bool
    
    class Config:
        from_attributes = True


class SessionAdvance(BaseModel):
    session_date: date = Field(..., description="תאריך השיעור שהתקיים")


class GenerateScheduleRequest(BaseModel):
    start_date: date = Field(..., description="תאריך התחלת המסלול")


# ============================================================
# Endpoints
# ============================================================

@router.get("/", response_model=List[CourseTrackResponse])
async def get_tracks(
    course_id: Optional[int] = None,
    lecturer_id: Optional[int] = None,
    city: Optional[str] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """קבלת כל המסלולים עם פילטרים"""
    await require_permission(current_user, "course_tracks", "view")
    
    tracks = await course_tracks.get_all_tracks(
        db=db,
        course_id=course_id,
        lecturer_id=lecturer_id,
        city=city,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    
    return tracks


@router.get("/upcoming-entry-points")
async def get_upcoming_entry_points(
    days_ahead: int = Query(30, description="כמה ימים קדימה לחפש"),
    course_id: Optional[int] = None,
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """קבלת נקודות כניסה קרובות - חשוב לאנשי מכירות"""
    await require_permission(current_user, "course_tracks", "view")
    
    entry_points = await course_tracks.get_upcoming_entry_points(
        db=db,
        days_ahead=days_ahead,
        course_id=course_id,
        city=city
    )
    
    return {"entry_points": entry_points}


@router.get("/{track_id}", response_model=CourseTrackResponse)
async def get_track(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """קבלת מסלול ספציפי"""
    await require_permission(current_user, "course_tracks", "view")
    
    track = await course_tracks.get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="מסלול לא נמצא")
    
    return track


@router.get("/{track_id}/progress")
async def get_track_progress(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """קבלת מידע על התקדמות המסלול"""
    await require_permission(current_user, "course_tracks", "view")
    
    progress = await course_tracks.get_track_progress(db, track_id)
    if not progress:
        raise HTTPException(status_code=404, detail="מסלול לא נמצא")
    
    return progress


@router.get("/{track_id}/sessions")
async def get_track_sessions(
    track_id: int,
    module_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """קבלת כל השיעורים של מסלול"""
    await require_permission(current_user, "course_tracks", "view")
    
    sessions = await course_sessions.get_track_sessions(
        db=db,
        track_id=track_id,
        module_id=module_id,
        from_date=from_date,
        to_date=to_date,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return {"sessions": sessions}


@router.post("/", response_model=CourseTrackResponse, status_code=201)
async def create_track(
    track_data: CourseTrackCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """יצירת מסלול חדש"""
    await require_permission(current_user, "course_tracks", "create")
    
    track = await course_tracks.create_track(
        db=db,
        course_id=track_data.course_id,
        lecturer_id=track_data.lecturer_id,
        name=track_data.name,
        day_of_week=track_data.day_of_week,
        start_time=track_data.start_time,
        city=track_data.city,
        zoom_url=track_data.zoom_url,
        price=track_data.price,
        current_module_id=track_data.current_module_id
    )
    
    return track


@router.put("/{track_id}", response_model=CourseTrackResponse)
async def update_track(
    track_id: int,
    track_data: CourseTrackUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """עדכון מסלול"""
    await require_permission(current_user, "course_tracks", "edit")
    
    update_data = track_data.model_dump(exclude_unset=True)
    track = await course_tracks.update_track(db, track_id, **update_data)
    
    if not track:
        raise HTTPException(status_code=404, detail="מסלול לא נמצא")
    
    return track


@router.delete("/{track_id}", status_code=204)
async def delete_track(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """מחיקת מסלול"""
    await require_permission(current_user, "course_tracks", "delete")
    
    success = await course_tracks.delete_track(db, track_id)
    if not success:
        raise HTTPException(status_code=404, detail="מסלול לא נמצא")
    
    return None


@router.post("/{track_id}/advance", response_model=CourseTrackResponse)
async def advance_track_session(
    track_id: int,
    advance_data: SessionAdvance,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """קידום המסלול למפגש הבא"""
    await require_permission(current_user, "course_tracks", "edit")
    
    track = await course_tracks.advance_track_session(
        db=db,
        track_id=track_id,
        session_date=advance_data.session_date
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="מסלול לא נמצא")
    
    return track


@router.post("/{track_id}/generate-schedule")
async def generate_track_schedule(
    track_id: int,
    schedule_data: GenerateScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """יצירת לוח זמנים מלא למסלול"""
    await require_permission(current_user, "course_tracks", "edit")
    
    sessions = await course_sessions.generate_full_track_schedule(
        db=db,
        track_id=track_id,
        start_date=schedule_data.start_date
    )
    
    return {
        "message": f"נוצרו {len(sessions)} שיעורים",
        "sessions_count": len(sessions),
        "sessions": sessions
    }


@router.post("/{track_id}/calculate-next-entry")
async def calculate_next_entry(
    track_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """חישוב תאריך נקודת הכניסה הבאה"""
    await require_permission(current_user, "course_tracks", "view")
    
    track = await course_tracks.get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="מסלול לא נמצא")
    
    next_entry = await course_tracks.calculate_next_entry_date(db, track)
    
    return {
        "track_id": track_id,
        "next_entry_date": next_entry
    }
