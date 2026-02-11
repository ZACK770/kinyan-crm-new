"""
Course Sessions Service - ניהול שיעורים מתוזמנים
שיעור = מפגש ספציפי במסלול בתאריך מסוים
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CourseSession, CourseTrack, CourseModule, Attendance


async def get_session(db: AsyncSession, session_id: int) -> Optional[CourseSession]:
    """קבלת שיעור לפי ID"""
    result = await db.execute(
        select(CourseSession)
        .options(
            selectinload(CourseSession.track),
            selectinload(CourseSession.module),
            selectinload(CourseSession.attendance_records)
        )
        .where(CourseSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_track_sessions(
    db: AsyncSession,
    track_id: int,
    module_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[CourseSession]:
    """קבלת כל השיעורים של מסלול"""
    query = select(CourseSession).options(
        selectinload(CourseSession.module),
        selectinload(CourseSession.attendance_records)
    ).where(CourseSession.track_id == track_id)
    
    filters = []
    if module_id:
        filters.append(CourseSession.module_id == module_id)
    if from_date:
        filters.append(CourseSession.session_date >= from_date)
    if to_date:
        filters.append(CourseSession.session_date <= to_date)
    if status:
        filters.append(CourseSession.status == status)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(CourseSession.session_date).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_session(
    db: AsyncSession,
    track_id: int,
    module_id: int,
    session_number: int,
    session_date: date,
    is_entry_point: bool = False,
    actual_start_time: Optional[str] = None,
    actual_end_time: Optional[str] = None,
    recording_url: Optional[str] = None,
    notes: Optional[str] = None,
    status: str = "מתוכנן"
) -> CourseSession:
    """יצירת שיעור חדש"""
    session = CourseSession(
        track_id=track_id,
        module_id=module_id,
        session_number=session_number,
        session_date=session_date,
        is_entry_point=is_entry_point,
        actual_start_time=actual_start_time,
        actual_end_time=actual_end_time,
        recording_url=recording_url,
        notes=notes,
        status=status
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


async def update_session(
    db: AsyncSession,
    session_id: int,
    **kwargs
) -> Optional[CourseSession]:
    """עדכון שיעור"""
    session = await get_session(db, session_id)
    if not session:
        return None
    
    for key, value in kwargs.items():
        if hasattr(session, key) and value is not None:
            setattr(session, key, value)
    
    await db.commit()
    await db.refresh(session)
    
    return session


async def delete_session(db: AsyncSession, session_id: int) -> bool:
    """מחיקת שיעור"""
    session = await get_session(db, session_id)
    if not session:
        return False
    
    await db.delete(session)
    await db.commit()
    return True


async def mark_session_completed(
    db: AsyncSession,
    session_id: int,
    recording_url: Optional[str] = None,
    notes: Optional[str] = None
) -> Optional[CourseSession]:
    """סימון שיעור כהתקיים"""
    session = await get_session(db, session_id)
    if not session:
        return None
    
    session.status = "התקיים"
    if recording_url:
        session.recording_url = recording_url
    if notes:
        session.notes = notes
    
    await db.commit()
    await db.refresh(session)
    
    return session


async def generate_sessions_for_module(
    db: AsyncSession,
    track_id: int,
    module_id: int,
    start_date: date,
    day_of_week: str
) -> List[CourseSession]:
    """
    יצירת כל השיעורים לחוברת מסוימת
    מחשב את התאריכים לפי יום השבוע
    """
    # קבלת המודול
    module_result = await db.execute(
        select(CourseModule).where(CourseModule.id == module_id)
    )
    module = module_result.scalar_one_or_none()
    
    if not module or not module.sessions_count:
        return []
    
    # מיפוי ימים לעברית
    day_mapping = {
        "ראשון": 6,  # Sunday
        "שני": 0,    # Monday
        "שלישי": 1,  # Tuesday
        "רביעי": 2,  # Wednesday
        "חמישי": 3,  # Thursday
        "שישי": 4,   # Friday
        "שבת": 5     # Saturday
    }
    
    target_weekday = day_mapping.get(day_of_week)
    if target_weekday is None:
        return []
    
    # חישוב התאריך הראשון
    current_date = start_date
    days_ahead = (target_weekday - current_date.weekday()) % 7
    if days_ahead == 0 and current_date > start_date:
        days_ahead = 7
    first_session_date = current_date + timedelta(days=days_ahead)
    
    # יצירת השיעורים
    sessions = []
    for i in range(module.sessions_count):
        session_date = first_session_date + timedelta(weeks=i)
        is_entry_point = (i == 0)  # השיעור הראשון הוא נקודת כניסה
        
        session = await create_session(
            db=db,
            track_id=track_id,
            module_id=module_id,
            session_number=i + 1,
            session_date=session_date,
            is_entry_point=is_entry_point,
            status="מתוכנן"
        )
        sessions.append(session)
    
    return sessions


async def generate_full_track_schedule(
    db: AsyncSession,
    track_id: int,
    start_date: date
) -> List[CourseSession]:
    """
    יצירת לוח זמנים מלא למסלול
    יוצר שיעורים לכל החוברות לפי הסילבוס
    """
    # קבלת המסלול
    track_result = await db.execute(
        select(CourseTrack)
        .options(selectinload(CourseTrack.course))
        .where(CourseTrack.id == track_id)
    )
    track = track_result.scalar_one_or_none()
    
    if not track:
        return []
    
    # קבלת כל החוברות במסלול
    modules_result = await db.execute(
        select(CourseModule)
        .where(CourseModule.course_id == track.course_id)
        .order_by(CourseModule.module_order)
    )
    modules = list(modules_result.scalars().all())
    
    all_sessions = []
    current_date = start_date
    
    for module in modules:
        if not module.sessions_count:
            continue
        
        # יצירת שיעורים לחוברת זו
        sessions = await generate_sessions_for_module(
            db=db,
            track_id=track_id,
            module_id=module.id,
            start_date=current_date,
            day_of_week=track.day_of_week
        )
        
        all_sessions.extend(sessions)
        
        # עדכון תאריך התחלה לחוברת הבאה
        if sessions:
            last_session_date = sessions[-1].session_date
            current_date = last_session_date + timedelta(weeks=1)
    
    return all_sessions


async def get_upcoming_sessions(
    db: AsyncSession,
    days_ahead: int = 7,
    track_id: Optional[int] = None,
    status: str = "מתוכנן"
) -> List[CourseSession]:
    """קבלת שיעורים קרובים"""
    filters = [
        CourseSession.session_date >= date.today(),
        CourseSession.session_date <= date.today() + timedelta(days=days_ahead),
        CourseSession.status == status
    ]
    
    if track_id:
        filters.append(CourseSession.track_id == track_id)
    
    result = await db.execute(
        select(CourseSession)
        .options(
            selectinload(CourseSession.track),
            selectinload(CourseSession.module)
        )
        .where(and_(*filters))
        .order_by(CourseSession.session_date)
    )
    
    return list(result.scalars().all())


async def get_entry_point_sessions(
    db: AsyncSession,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    track_id: Optional[int] = None
) -> List[CourseSession]:
    """קבלת כל נקודות הכניסה (שיעורים ראשונים של חוברות)"""
    filters = [CourseSession.is_entry_point == True]
    
    if from_date:
        filters.append(CourseSession.session_date >= from_date)
    if to_date:
        filters.append(CourseSession.session_date <= to_date)
    if track_id:
        filters.append(CourseSession.track_id == track_id)
    
    result = await db.execute(
        select(CourseSession)
        .options(
            selectinload(CourseSession.track),
            selectinload(CourseSession.module)
        )
        .where(and_(*filters))
        .order_by(CourseSession.session_date)
    )
    
    return list(result.scalars().all())


async def get_session_attendance_summary(
    db: AsyncSession,
    session_id: int
) -> Optional[dict]:
    """קבלת סיכום נוכחות לשיעור"""
    session = await get_session(db, session_id)
    if not session:
        return None
    
    # ספירת נוכחות
    attendance_records = session.attendance_records
    total_students = len(attendance_records)
    present_count = sum(1 for a in attendance_records if a.is_present)
    absent_count = total_students - present_count
    
    # ספירת מטלות
    assignments_done = sum(1 for a in attendance_records if a.assignment_done)
    
    return {
        "session_id": session.id,
        "session_date": session.session_date,
        "module_name": session.module.name if session.module else None,
        "session_number": session.session_number,
        "status": session.status,
        "total_students": total_students,
        "present_count": present_count,
        "absent_count": absent_count,
        "attendance_rate": round((present_count / total_students * 100) if total_students > 0 else 0, 1),
        "assignments_done": assignments_done,
        "assignment_completion_rate": round((assignments_done / total_students * 100) if total_students > 0 else 0, 1)
    }
