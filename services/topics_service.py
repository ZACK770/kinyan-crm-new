import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db.models import Topic, Lesson, StudentLessonProgress, Course, Student
import logging

logger = logging.getLogger(__name__)


async def get_course_topics(db: AsyncSession, course_id: int) -> List[Topic]:
    result = await db.execute(
        select(Topic)
        .where(Topic.course_id == course_id)
        .order_by(Topic.order_index)
        .options(selectinload(Topic.lessons))
    )
    return result.scalars().all()


async def get_topic_by_id(db: AsyncSession, topic_id: int) -> Optional[Topic]:
    result = await db.execute(
        select(Topic)
        .where(Topic.id == topic_id)
        .options(selectinload(Topic.lessons))
    )
    return result.scalar_one_or_none()


async def reorder_topics(db: AsyncSession, course_id: int, new_order: List[int]) -> bool:
    existing_topics = await get_course_topics(db, course_id)
    existing_ids = {t.id for t in existing_topics}
    
    if set(new_order) != existing_ids:
        raise ValueError("Invalid topic IDs in new order")
    
    for index, topic_id in enumerate(new_order):
        result = await db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        topic = result.scalar_one()
        topic.order_index = index
    
    course_result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = course_result.scalar_one()
    course.topics_order = json.dumps(new_order)
    
    await db.flush()
    return True


async def get_topic_lessons(db: AsyncSession, topic_id: int) -> List[Lesson]:
    result = await db.execute(
        select(Lesson)
        .where(Lesson.topic_id == topic_id)
        .order_by(Lesson.lesson_number)
    )
    return result.scalars().all()


async def get_lesson_by_id(db: AsyncSession, lesson_id: int) -> Optional[Lesson]:
    result = await db.execute(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.progress_records))
    )
    return result.scalar_one_or_none()


async def get_current_running_topic(db: AsyncSession, course_id: int, city: Optional[str] = None) -> Optional[Topic]:
    now = datetime.now()
    
    result = await db.execute(
        select(Lesson)
        .join(Topic)
        .where(
            and_(
                Lesson.course_id == course_id,
                Lesson.scheduled_date <= now,
                Lesson.status == "scheduled"
            )
        )
        .order_by(Lesson.scheduled_date.desc())
        .limit(1)
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        return None
    
    return await get_topic_by_id(db, lesson.topic_id)


async def get_current_lesson_in_topic(db: AsyncSession, topic_id: int) -> Optional[Lesson]:
    now = datetime.now()
    
    result = await db.execute(
        select(Lesson)
        .where(
            and_(
                Lesson.topic_id == topic_id,
                Lesson.scheduled_date <= now
            )
        )
        .order_by(Lesson.scheduled_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def count_lessons_remaining_in_topic(db: AsyncSession, topic_id: int, current_lesson_number: int) -> int:
    result = await db.execute(
        select(func.count(Lesson.id))
        .where(
            and_(
                Lesson.topic_id == topic_id,
                Lesson.lesson_number > current_lesson_number
            )
        )
    )
    return result.scalar() or 0


async def get_next_topic_in_loop(db: AsyncSession, course_id: int, current_order_index: int) -> Optional[Topic]:
    result = await db.execute(
        select(Topic)
        .where(Topic.course_id == course_id)
        .order_by(Topic.order_index)
    )
    topics = result.scalars().all()
    
    if not topics:
        return None
    
    next_index = (current_order_index + 1) % len(topics)
    
    for topic in topics:
        if topic.order_index == next_index:
            return topic
    
    return None


async def get_first_lesson_of_topic(db: AsyncSession, topic_id: int) -> Optional[Lesson]:
    result = await db.execute(
        select(Lesson)
        .where(Lesson.topic_id == topic_id)
        .order_by(Lesson.lesson_number)
        .limit(1)
    )
    return result.scalar_one_or_none()


def calculate_entry_date(current_lesson_date: datetime, lessons_remaining: int, days_between_lessons: int = 7) -> datetime:
    return current_lesson_date + timedelta(days=lessons_remaining * days_between_lessons)


async def get_next_entry_point(db: AsyncSession, course_id: int, city: Optional[str] = None) -> Dict[str, Any]:
    current_topic = await get_current_running_topic(db, course_id, city)
    
    if not current_topic:
        return {
            "error": "No active topic found for this course",
            "entry_lesson_id": None,
            "entry_date": None
        }
    
    current_lesson = await get_current_lesson_in_topic(db, current_topic.id)
    
    if not current_lesson:
        return {
            "error": "No current lesson found",
            "entry_lesson_id": None,
            "entry_date": None
        }
    
    lessons_remaining = await count_lessons_remaining_in_topic(db, current_topic.id, current_lesson.lesson_number)
    
    next_topic = await get_next_topic_in_loop(db, course_id, current_topic.order_index)
    
    if not next_topic:
        return {
            "error": "No next topic found",
            "entry_lesson_id": None,
            "entry_date": None
        }
    
    next_entry_lesson = await get_first_lesson_of_topic(db, next_topic.id)
    
    if not next_entry_lesson:
        return {
            "error": "No lessons in next topic",
            "entry_lesson_id": None,
            "entry_date": None
        }
    
    estimated_entry_date = calculate_entry_date(current_lesson.scheduled_date, lessons_remaining)
    
    return {
        "entry_lesson_id": next_entry_lesson.id,
        "entry_date": estimated_entry_date.isoformat(),
        "topic_name": next_topic.name,
        "lessons_until_entry": lessons_remaining,
        "current_topic": current_topic.name,
        "current_lesson_number": current_lesson.lesson_number,
        "current_lesson_title": current_lesson.title
    }


async def is_topic_completed_by_student(db: AsyncSession, student_id: int, topic_id: int, threshold: float = 0.8) -> bool:
    lessons = await get_topic_lessons(db, topic_id)
    
    if not lessons:
        return False
    
    lesson_ids = [l.id for l in lessons]
    
    result = await db.execute(
        select(StudentLessonProgress)
        .where(
            and_(
                StudentLessonProgress.student_id == student_id,
                StudentLessonProgress.lesson_id.in_(lesson_ids)
            )
        )
    )
    progress_records = result.scalars().all()
    
    completed_count = sum(
        1 for p in progress_records
        if p.attended or p.video_watch_percentage >= 80
    )
    
    return completed_count >= (len(lessons) * threshold)


async def calculate_student_status(db: AsyncSession, student_id: int) -> Dict[str, Any]:
    student_result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = student_result.scalar_one_or_none()
    
    if not student or not student.entry_point_lesson_id:
        return {
            "error": "Student not found or no entry point set",
            "is_graduate": False,
            "progress_percentage": 0
        }
    
    entry_lesson = await get_lesson_by_id(db, student.entry_point_lesson_id)
    
    if not entry_lesson:
        return {
            "error": "Entry lesson not found",
            "is_graduate": False,
            "progress_percentage": 0
        }
    
    entry_topic_result = await db.execute(
        select(Topic).where(Topic.id == entry_lesson.topic_id)
    )
    entry_topic = entry_topic_result.scalar_one()
    
    course_topics = await get_course_topics(db, entry_topic.course_id)
    
    entry_index = entry_topic.order_index
    required_topics = course_topics[entry_index:] + course_topics[:entry_index]
    
    completed_topics = []
    for topic in required_topics:
        if await is_topic_completed_by_student(db, student_id, topic.id):
            completed_topics.append(topic.id)
        else:
            break
    
    progress_percentage = (len(completed_topics) / len(required_topics)) * 100 if required_topics else 0
    is_graduate = len(completed_topics) == len(required_topics)
    
    current_topic = None
    if not is_graduate and len(completed_topics) < len(required_topics):
        current_topic = required_topics[len(completed_topics)]
    
    return {
        "is_graduate": is_graduate,
        "progress_percentage": round(progress_percentage, 2),
        "completed_topics": len(completed_topics),
        "total_topics": len(required_topics),
        "current_topic": {
            "id": current_topic.id,
            "name": current_topic.name
        } if current_topic else None
    }


async def get_student_progress_for_lesson(db: AsyncSession, student_id: int, lesson_id: int) -> Optional[StudentLessonProgress]:
    result = await db.execute(
        select(StudentLessonProgress)
        .where(
            and_(
                StudentLessonProgress.student_id == student_id,
                StudentLessonProgress.lesson_id == lesson_id
            )
        )
    )
    return result.scalar_one_or_none()


async def update_student_progress(
    db: AsyncSession,
    student_id: int,
    lesson_id: int,
    attended: Optional[bool] = None,
    video_watch_percentage: Optional[int] = None,
    assignment_submitted: Optional[bool] = None,
    assignment_file_url: Optional[str] = None,
    assignment_grade: Optional[int] = None,
    assignment_feedback: Optional[str] = None
) -> StudentLessonProgress:
    progress = await get_student_progress_for_lesson(db, student_id, lesson_id)
    
    if not progress:
        progress = StudentLessonProgress(
            student_id=student_id,
            lesson_id=lesson_id
        )
        db.add(progress)
    
    if attended is not None:
        progress.attended = attended
        if attended:
            progress.attendance_date = datetime.now()
    
    if video_watch_percentage is not None:
        progress.video_watch_percentage = video_watch_percentage
        progress.video_watched = video_watch_percentage >= 80
        progress.last_watched_at = datetime.now()
    
    if assignment_submitted is not None:
        progress.assignment_submitted = assignment_submitted
        if assignment_submitted:
            progress.assignment_submitted_at = datetime.now()
    
    if assignment_file_url is not None:
        progress.assignment_file_url = assignment_file_url
    
    if assignment_grade is not None:
        progress.assignment_grade = assignment_grade
    
    if assignment_feedback is not None:
        progress.assignment_feedback = assignment_feedback
    
    await db.flush()
    return progress


async def get_lesson_students_progress(db: AsyncSession, lesson_id: int) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(StudentLessonProgress)
        .where(StudentLessonProgress.lesson_id == lesson_id)
        .options(selectinload(StudentLessonProgress.student))
    )
    progress_records = result.scalars().all()
    
    return [
        {
            "student_id": p.student_id,
            "full_name": p.student.full_name if p.student else "Unknown",
            "attended": p.attended,
            "video_watched": p.video_watched,
            "video_watch_percentage": p.video_watch_percentage,
            "assignment_submitted": p.assignment_submitted,
            "assignment_grade": p.assignment_grade
        }
        for p in progress_records
    ]
