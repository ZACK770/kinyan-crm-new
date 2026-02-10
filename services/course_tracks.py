"""
Course Tracks Service - ניהול מסלולי לימוד
מסלול = קורס ספציפי עם מרצה, יום, שעה, עיר
כולל חישוב נקודות כניסה אוטומטי
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CourseTrack, Course, Lecturer, CourseModule, CourseSession


async def get_track(db: AsyncSession, track_id: int) -> Optional[CourseTrack]:
    """קבלת מסלול לפי ID"""
    result = await db.execute(
        select(CourseTrack)
        .options(
            selectinload(CourseTrack.course),
            selectinload(CourseTrack.lecturer),
            selectinload(CourseTrack.current_module),
            selectinload(CourseTrack.sessions)
        )
        .where(CourseTrack.id == track_id)
    )
    return result.scalar_one_or_none()


async def get_all_tracks(
    db: AsyncSession,
    course_id: Optional[int] = None,
    lecturer_id: Optional[int] = None,
    city: Optional[str] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100
) -> List[CourseTrack]:
    """קבלת כל המסלולים עם פילטרים"""
    query = select(CourseTrack).options(
        selectinload(CourseTrack.course),
        selectinload(CourseTrack.lecturer),
        selectinload(CourseTrack.current_module)
    )
    
    filters = []
    if course_id:
        filters.append(CourseTrack.course_id == course_id)
    if lecturer_id:
        filters.append(CourseTrack.lecturer_id == lecturer_id)
    if city:
        filters.append(CourseTrack.city == city)
    if is_active is not None:
        filters.append(CourseTrack.is_active == is_active)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(CourseTrack.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_track(
    db: AsyncSession,
    course_id: int,
    lecturer_id: int,
    name: str,
    day_of_week: str,
    start_time: str,
    city: str,
    zoom_url: Optional[str] = None,
    price: Optional[float] = None,
    current_module_id: Optional[int] = None
) -> CourseTrack:
    """יצירת מסלול חדש"""
    track = CourseTrack(
        course_id=course_id,
        lecturer_id=lecturer_id,
        name=name,
        day_of_week=day_of_week,
        start_time=start_time,
        city=city,
        zoom_url=zoom_url,
        price=price,
        current_module_id=current_module_id,
        current_session_number=1,
        is_active=True
    )
    
    db.add(track)
    await db.commit()
    await db.refresh(track)
    
    return track


async def update_track(
    db: AsyncSession,
    track_id: int,
    **kwargs
) -> Optional[CourseTrack]:
    """עדכון מסלול"""
    track = await get_track(db, track_id)
    if not track:
        return None
    
    for key, value in kwargs.items():
        if hasattr(track, key) and value is not None:
            setattr(track, key, value)
    
    await db.commit()
    await db.refresh(track)
    
    return track


async def delete_track(db: AsyncSession, track_id: int) -> bool:
    """מחיקת מסלול"""
    track = await get_track(db, track_id)
    if not track:
        return False
    
    await db.delete(track)
    await db.commit()
    return True


async def calculate_next_entry_date(
    db: AsyncSession,
    track: CourseTrack
) -> Optional[date]:
    """
    חישוב תאריך נקודת הכניסה הבאה
    נוסחה: מה החוברת הנוכחית + כמה מפגשים נותרו + יום השיעור
    """
    if not track.current_module_id:
        return None
    
    # קבלת החוברת הנוכחית
    result = await db.execute(
        select(CourseModule).where(CourseModule.id == track.current_module_id)
    )
    current_module = result.scalar_one_or_none()
    
    if not current_module or not current_module.sessions_count:
        return None
    
    # חישוב מפגשים נותרים בחוברת הנוכחית
    sessions_remaining = current_module.sessions_count - track.current_session_number + 1
    
    # אם נשארו מפגשים בחוברת הנוכחית, אין נקודת כניסה קרובה
    if sessions_remaining > 1:
        # נקודת הכניסה הבאה היא בתחילת החוברת הבאה
        weeks_until_next_module = sessions_remaining
        if track.last_session_date:
            next_entry = track.last_session_date + timedelta(weeks=weeks_until_next_module)
        else:
            # אם אין תאריך שיעור אחרון, נחשב מהיום
            next_entry = date.today() + timedelta(weeks=weeks_until_next_module)
        return next_entry
    
    # אם זה המפגש האחרון בחוברת, נקודת הכניסה היא בשבוע הבא
    if track.last_session_date:
        return track.last_session_date + timedelta(weeks=1)
    
    return date.today() + timedelta(weeks=1)


async def advance_track_session(
    db: AsyncSession,
    track_id: int,
    session_date: date
) -> Optional[CourseTrack]:
    """
    קידום המסלול למפגש הבא
    מעדכן את current_session_number ו-last_session_date
    אם מסיימים חוברת, עובר לחוברת הבאה
    """
    track = await get_track(db, track_id)
    if not track:
        return None
    
    # עדכון תאריך שיעור אחרון
    track.last_session_date = session_date
    
    # קבלת החוברת הנוכחית
    if not track.current_module_id:
        await db.commit()
        return track
    
    result = await db.execute(
        select(CourseModule).where(CourseModule.id == track.current_module_id)
    )
    current_module = result.scalar_one_or_none()
    
    if not current_module:
        await db.commit()
        return track
    
    # האם סיימנו את החוברת?
    if current_module.sessions_count and track.current_session_number >= current_module.sessions_count:
        # מעבר לחוברת הבאה
        next_module_result = await db.execute(
            select(CourseModule)
            .where(
                and_(
                    CourseModule.course_id == track.course_id,
                    CourseModule.module_order == current_module.module_order + 1
                )
            )
        )
        next_module = next_module_result.scalar_one_or_none()
        
        if next_module:
            track.current_module_id = next_module.id
            track.current_session_number = 1
        else:
            # אין חוברת הבאה - חזרה לתחילת המסלול (מחזורי)
            first_module_result = await db.execute(
                select(CourseModule)
                .where(CourseModule.course_id == track.course_id)
                .order_by(CourseModule.module_order)
                .limit(1)
            )
            first_module = first_module_result.scalar_one_or_none()
            if first_module:
                track.current_module_id = first_module.id
                track.current_session_number = 1
    else:
        # קידום למפגש הבא באותה חוברת
        track.current_session_number += 1
    
    # חישוב נקודת כניסה הבאה
    track.next_entry_date = await calculate_next_entry_date(db, track)
    
    await db.commit()
    await db.refresh(track)
    
    return track


async def get_upcoming_entry_points(
    db: AsyncSession,
    days_ahead: int = 30,
    course_id: Optional[int] = None,
    city: Optional[str] = None
) -> List[dict]:
    """
    קבלת נקודות כניסה קרובות
    מחזיר רשימת מסלולים עם תאריך נקודת הכניסה הבאה
    """
    filters = [
        CourseTrack.is_active == True,
        CourseTrack.next_entry_date.isnot(None),
        CourseTrack.next_entry_date <= date.today() + timedelta(days=days_ahead)
    ]
    
    if course_id:
        filters.append(CourseTrack.course_id == course_id)
    if city:
        filters.append(CourseTrack.city == city)
    
    result = await db.execute(
        select(CourseTrack)
        .options(
            selectinload(CourseTrack.course),
            selectinload(CourseTrack.lecturer),
            selectinload(CourseTrack.current_module)
        )
        .where(and_(*filters))
        .order_by(CourseTrack.next_entry_date)
    )
    
    tracks = result.scalars().all()
    
    return [
        {
            "track_id": track.id,
            "track_name": track.name,
            "course_name": track.course.name if track.course else None,
            "lecturer_name": track.lecturer.name if track.lecturer else None,
            "city": track.city,
            "day_of_week": track.day_of_week,
            "start_time": track.start_time,
            "next_entry_date": track.next_entry_date,
            "current_module_name": track.current_module.name if track.current_module else None,
            "price": float(track.price) if track.price else None,
            "zoom_url": track.zoom_url
        }
        for track in tracks
    ]


async def get_track_progress(db: AsyncSession, track_id: int) -> Optional[dict]:
    """קבלת מידע על התקדמות המסלול"""
    track = await get_track(db, track_id)
    if not track:
        return None
    
    # קבלת כל החוברות במסלול
    modules_result = await db.execute(
        select(CourseModule)
        .where(CourseModule.course_id == track.course_id)
        .order_by(CourseModule.module_order)
    )
    modules = list(modules_result.scalars().all())
    
    # חישוב סה"כ מפגשים במסלול
    total_sessions = sum(m.sessions_count or 0 for m in modules)
    
    # חישוב מפגשים שהושלמו
    completed_sessions = 0
    for module in modules:
        if not track.current_module_id:
            break
        if module.id == track.current_module_id:
            completed_sessions += track.current_session_number - 1
            break
        completed_sessions += module.sessions_count or 0
    
    return {
        "track_id": track.id,
        "track_name": track.name,
        "total_modules": len(modules),
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "current_module": track.current_module.name if track.current_module else None,
        "current_session_number": track.current_session_number,
        "last_session_date": track.last_session_date,
        "next_entry_date": track.next_entry_date,
        "progress_percentage": round((completed_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1)
    }
