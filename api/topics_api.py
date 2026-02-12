import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from db import get_db
from db.models import User, Topic, Lesson, StudentLessonProgress, Course, Student
from api.dependencies import get_current_user
from services import topics_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────

class CreateTopicRequest(BaseModel):
    name: str
    description: Optional[str] = None


class CreateLessonRequest(BaseModel):
    title: str
    description: Optional[str] = None
    lecturer_name: Optional[str] = None
    scheduled_date: Optional[datetime] = None


class ReorderTopicsRequest(BaseModel):
    new_order: List[int]


class UpdateProgressRequest(BaseModel):
    attended: Optional[bool] = None
    video_watch_percentage: Optional[int] = None
    assignment_submitted: Optional[bool] = None
    assignment_file_url: Optional[str] = None
    assignment_grade: Optional[int] = None
    assignment_feedback: Optional[str] = None


class UpdateLessonRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    lecturer_name: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    status: Optional[str] = None
    assignment_title: Optional[str] = None
    assignment_description: Optional[str] = None
    assignment_file_url: Optional[str] = None
    assignment_due_days: Optional[int] = None


def _check_permission(user: User, min_level: int = 20):
    if user.permission_level < min_level:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("/courses/{course_id}/topics")
async def get_course_topics(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 10)
    
    topics = await topics_service.get_course_topics(db, course_id)
    
    result = []
    for topic in topics:
        first_lesson = None
        if topic.lessons:
            first = topic.lessons[0]
            first_lesson = {
                "id": first.id,
                "title": first.title,
                "scheduled_date": first.scheduled_date.isoformat() if first.scheduled_date else None
            }
        
        result.append({
            "id": topic.id,
            "name": topic.name,
            "description": topic.description,
            "order_index": topic.order_index,
            "lessons_count": topic.lessons_count,
            "first_lesson": first_lesson
        })
    
    return {
        "success": True,
        "topics": result
    }


@router.post("/courses/{course_id}/topics")
async def create_topic(
    course_id: int,
    request: CreateTopicRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 30)
    
    try:
        # Get max order_index
        result = await db.execute(
            select(func.coalesce(func.max(Topic.order_index), -1))
            .where(Topic.course_id == course_id)
        )
        max_index = result.scalar()
        
        topic = Topic(
            course_id=course_id,
            name=request.name,
            description=request.description,
            order_index=max_index + 1,
            lessons_count=0
        )
        db.add(topic)
        await db.commit()
        await db.refresh(topic)
        
        return {
            "success": True,
            "topic": {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "order_index": topic.order_index,
                "lessons_count": 0,
                "first_lesson": None
            }
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create topic for course {course_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create topic: {str(e)}")


@router.delete("/topics/{topic_id}")
async def delete_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 30)
    
    topic = await topics_service.get_topic_by_id(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    await db.delete(topic)
    await db.commit()
    
    return {"success": True, "message": "Topic deleted"}


@router.post("/courses/{course_id}/topics/reorder")
async def reorder_course_topics(
    course_id: int,
    request: ReorderTopicsRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 30)
    
    try:
        success = await topics_service.reorder_topics(db, course_id, request.new_order)
        await db.commit()
        
        return {
            "success": success,
            "message": "Topics reordered successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reorder topics: {str(e)}")


@router.get("/topics/{topic_id}/lessons")
async def get_topic_lessons(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 10)
    
    topic = await topics_service.get_topic_by_id(db, topic_id)
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    lessons = await topics_service.get_topic_lessons(db, topic_id)
    
    result = []
    for lesson in lessons:
        students_progress = await topics_service.get_lesson_students_progress(db, lesson.id)
        submitted_count = sum(1 for p in students_progress if p["assignment_submitted"])
        
        result.append({
            "id": lesson.id,
            "lesson_number": lesson.lesson_number,
            "title": lesson.title,
            "description": lesson.description,
            "video_url": lesson.video_url,
            "cover_image_url": lesson.cover_image_url,
            "lecturer_name": lesson.lecturer_name,
            "scheduled_date": lesson.scheduled_date.isoformat() if lesson.scheduled_date else None,
            "status": lesson.status,
            "assignment_title": lesson.assignment_title,
            "students_count": len(students_progress),
            "assignment_submitted_count": submitted_count
        })
    
    return {
        "success": True,
        "topic": {
            "id": topic.id,
            "name": topic.name,
            "course_id": topic.course_id
        },
        "lessons": result
    }


@router.post("/topics/{topic_id}/lessons")
async def create_lesson(
    topic_id: int,
    request: CreateLessonRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 30)
    
    topic = await topics_service.get_topic_by_id(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Get max lesson_number
    result = await db.execute(
        select(func.coalesce(func.max(Lesson.lesson_number), 0))
        .where(Lesson.topic_id == topic_id)
    )
    max_num = result.scalar()
    
    lesson = Lesson(
        topic_id=topic_id,
        course_id=topic.course_id,
        lesson_number=max_num + 1,
        title=request.title,
        description=request.description,
        lecturer_name=request.lecturer_name,
        scheduled_date=request.scheduled_date,
        status="scheduled"
    )
    db.add(lesson)
    
    # Update topic lessons_count
    topic.lessons_count = max_num + 1
    
    await db.commit()
    await db.refresh(lesson)
    
    return {
        "success": True,
        "lesson": {
            "id": lesson.id,
            "lesson_number": lesson.lesson_number,
            "title": lesson.title,
            "status": lesson.status
        }
    }


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 30)
    
    lesson = await topics_service.get_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    await db.delete(lesson)
    await db.commit()
    
    return {"success": True, "message": "Lesson deleted"}


@router.get("/courses/{course_id}/entry-points")
async def get_course_entry_points(
    course_id: int,
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 10)
    
    entry_point = await topics_service.get_next_entry_point(db, course_id, city)
    
    if "error" in entry_point:
        return {
            "success": False,
            "error": entry_point["error"]
        }
    
    current_topic = await topics_service.get_current_running_topic(db, course_id, city)
    current_lesson = None
    if current_topic:
        current_lesson = await topics_service.get_current_lesson_in_topic(db, current_topic.id)
    
    return {
        "success": True,
        "current_status": {
            "current_topic": entry_point.get("current_topic"),
            "current_lesson_number": entry_point.get("current_lesson_number"),
            "current_lesson_title": entry_point.get("current_lesson_title"),
            "lessons_remaining_in_topic": entry_point.get("lessons_until_entry")
        },
        "next_entry_point": {
            "entry_lesson_id": entry_point["entry_lesson_id"],
            "entry_date": entry_point["entry_date"],
            "topic_name": entry_point["topic_name"],
            "lessons_until_entry": entry_point["lessons_until_entry"]
        }
    }


@router.get("/students/{student_id}/progress")
async def get_student_progress(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 10)
    
    status = await topics_service.calculate_student_status(db, student_id)
    
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return {
        "success": True,
        "progress": status
    }


@router.post("/students/{student_id}/lessons/{lesson_id}/progress")
async def update_lesson_progress(
    student_id: int,
    lesson_id: int,
    request: UpdateProgressRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 20)
    
    try:
        progress = await topics_service.update_student_progress(
            db=db,
            student_id=student_id,
            lesson_id=lesson_id,
            attended=request.attended,
            video_watch_percentage=request.video_watch_percentage,
            assignment_submitted=request.assignment_submitted,
            assignment_file_url=request.assignment_file_url,
            assignment_grade=request.assignment_grade,
            assignment_feedback=request.assignment_feedback
        )
        await db.commit()
        
        return {
            "success": True,
            "progress_updated": True,
            "progress": {
                "attended": progress.attended,
                "video_watched": progress.video_watched,
                "video_watch_percentage": progress.video_watch_percentage,
                "assignment_submitted": progress.assignment_submitted,
                "assignment_grade": progress.assignment_grade
            }
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")


@router.get("/lessons/{lesson_id}/workspace")
async def get_lesson_workspace(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 20)
    
    lesson = await topics_service.get_lesson_by_id(db, lesson_id)
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    topic = await topics_service.get_topic_by_id(db, lesson.topic_id)
    students_progress = await topics_service.get_lesson_students_progress(db, lesson_id)
    
    submitted_count = sum(1 for p in students_progress if p["assignment_submitted"])
    
    return {
        "success": True,
        "lesson": {
            "id": lesson.id,
            "title": lesson.title,
            "topic_name": topic.name if topic else None,
            "course_id": lesson.course_id,
            "lesson_number": lesson.lesson_number,
            "scheduled_date": lesson.scheduled_date.isoformat() if lesson.scheduled_date else None,
            "actual_date": lesson.actual_date.isoformat() if lesson.actual_date else None,
            "video_url": lesson.video_url,
            "video_duration": lesson.video_duration,
            "lecturer_name": lesson.lecturer_name,
            "cover_image_url": lesson.cover_image_url,
            "description": lesson.description,
            "status": lesson.status
        },
        "assignment": {
            "title": lesson.assignment_title,
            "description": lesson.assignment_description,
            "file_url": lesson.assignment_file_url,
            "due_days": lesson.assignment_due_days,
            "submitted_count": submitted_count,
            "total_students": len(students_progress)
        },
        "students": students_progress
    }


@router.put("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: int,
    request: UpdateLessonRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 30)
    
    lesson = await topics_service.get_lesson_by_id(db, lesson_id)
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    try:
        if request.title is not None:
            lesson.title = request.title
        if request.description is not None:
            lesson.description = request.description
        if request.video_url is not None:
            lesson.video_url = request.video_url
        if request.cover_image_url is not None:
            lesson.cover_image_url = request.cover_image_url
        if request.lecturer_name is not None:
            lesson.lecturer_name = request.lecturer_name
        if request.scheduled_date is not None:
            lesson.scheduled_date = request.scheduled_date
        if request.actual_date is not None:
            lesson.actual_date = request.actual_date
        if request.status is not None:
            lesson.status = request.status
        if request.assignment_title is not None:
            lesson.assignment_title = request.assignment_title
        if request.assignment_description is not None:
            lesson.assignment_description = request.assignment_description
        if request.assignment_file_url is not None:
            lesson.assignment_file_url = request.assignment_file_url
        if request.assignment_due_days is not None:
            lesson.assignment_due_days = request.assignment_due_days
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Lesson updated successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update lesson: {str(e)}")


# ── Student Portal ──────────────────────────────────────────

@router.get("/student-portal/{student_id}/{course_id}")
async def get_student_portal(
    student_id: int,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_permission(user, 10)
    
    # Get student
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get course
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get topics
    topics = await topics_service.get_course_topics(db, course_id)
    
    # Get all lesson IDs for this course
    all_lessons = []
    topics_data = []
    for topic in topics:
        topic_lessons = await topics_service.get_topic_lessons(db, topic.id)
        lessons_data = []
        for lesson in topic_lessons:
            # Get progress for this student
            progress = await topics_service.get_student_progress_for_lesson(db, student_id, lesson.id)
            lessons_data.append({
                "id": lesson.id,
                "lesson_number": lesson.lesson_number,
                "title": lesson.title,
                "description": lesson.description,
                "video_url": lesson.video_url,
                "cover_image_url": lesson.cover_image_url,
                "lecturer_name": lesson.lecturer_name,
                "scheduled_date": lesson.scheduled_date.isoformat() if lesson.scheduled_date else None,
                "assignment_title": lesson.assignment_title,
                "assignment_description": lesson.assignment_description,
                "assignment_file_url": lesson.assignment_file_url,
                "assignment_due_days": lesson.assignment_due_days or 7,
                "progress": {
                    "attended": progress.attended,
                    "video_watched": progress.video_watched,
                    "video_watch_percentage": progress.video_watch_percentage,
                    "assignment_submitted": progress.assignment_submitted,
                    "assignment_grade": progress.assignment_grade
                } if progress else None
            })
            all_lessons.append(lesson)
        
        topics_data.append({
            "id": topic.id,
            "name": topic.name,
            "order_index": topic.order_index,
            "lessons_count": len(topic_lessons),
            "lessons": lessons_data
        })
    
    # Calculate overall progress
    total_lessons = len(all_lessons)
    completed_lessons = 0
    if total_lessons > 0:
        for lesson in all_lessons:
            progress = await topics_service.get_student_progress_for_lesson(db, student_id, lesson.id)
            if progress and (progress.attended or progress.video_watch_percentage >= 80):
                completed_lessons += 1
    
    progress_pct = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    return {
        "success": True,
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "is_graduate": student.is_graduate
        },
        "course": {
            "id": course.id,
            "name": course.name
        },
        "topics": topics_data,
        "progress": {
            "completed_lessons": completed_lessons,
            "total_lessons": total_lessons,
            "percentage": round(progress_pct, 1),
            "is_graduate": student.is_graduate
        }
    }
