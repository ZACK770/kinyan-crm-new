"""
Student management service.
Handles conversion from lead → student, enrollments, progress tracking.
"""
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Student, Lead, Enrollment, Course, CourseModule


async def create_from_lead(db: AsyncSession, lead_id: int) -> Student:
    """Convert a lead to a student (copies basic info)."""
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    student = Student(
        full_name=lead.full_name,
        phone=lead.phone,
        phone2=lead.phone2,
        email=lead.email,
        address=lead.address,
        city=lead.city,
        id_number=lead.id_number,
        lead_id=lead.id,
    )
    db.add(student)
    await db.flush()

    # Update lead
    lead.student_id = student.id
    lead.status = "ליד סגור - לקוח"
    lead.conversion_date = func.now()
    await db.flush()

    return student


async def enroll_in_course(
    db: AsyncSession,
    student_id: int,
    course_id: int,
    entry_module_order: int = 1,
    start_date: date | None = None,
) -> Enrollment:
    """Enroll a student in a course with a specific entry point."""
    # Get course and count modules
    course_stmt = select(Course).where(Course.id == course_id).options(selectinload(Course.modules))
    course_result = await db.execute(course_stmt)
    course = course_result.scalar_one_or_none()
    if not course:
        raise ValueError(f"Course {course_id} not found")

    total_modules = len(course.modules)

    # Calculate remaining sessions
    remaining_sessions = 0
    for m in course.modules:
        if m.module_order >= entry_module_order:
            remaining_sessions += (m.sessions_count or 0)

    # Estimate finish date (~2 sessions per week)
    days_to_finish = remaining_sessions * 3.5  # ~2 sessions/week = 3.5 days per session
    est_finish = (start_date or date.today()) + timedelta(days=int(days_to_finish))

    # Find entry module
    entry_module = None
    for m in course.modules:
        if m.module_order == entry_module_order:
            entry_module = m
            break

    enrollment = Enrollment(
        student_id=student_id,
        course_id=course_id,
        enrollment_date=date.today(),
        entry_module_id=entry_module.id if entry_module else None,
        start_date=start_date or date.today(),
        current_module=entry_module_order,
        total_modules=total_modules,
        sessions_remaining=remaining_sessions,
        estimated_finish=est_finish,
        status="פעיל",
    )
    db.add(enrollment)
    await db.flush()
    return enrollment


async def update_progress(
    db: AsyncSession,
    enrollment_id: int,
    current_module: int,
) -> Enrollment | None:
    """Update student progress in a course."""
    stmt = select(Enrollment).where(Enrollment.id == enrollment_id).options(
        selectinload(Enrollment.course).selectinload(Course.modules)
    )
    result = await db.execute(stmt)
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        return None

    enrollment.current_module = current_module

    # Recalculate remaining
    remaining = 0
    for m in enrollment.course.modules:
        if m.module_order >= current_module:
            remaining += (m.sessions_count or 0)
    enrollment.sessions_remaining = remaining

    # Recalculate finish
    days_left = remaining * 3.5
    enrollment.estimated_finish = date.today() + timedelta(days=int(days_left))

    if current_module > (enrollment.total_modules or 0):
        enrollment.status = "הושלם"

    await db.flush()
    return enrollment


async def get_student_dashboard(db: AsyncSession, student_id: int) -> dict | None:
    """Get full student info with enrollments and exams."""
    stmt = (
        select(Student)
        .where(Student.id == student_id)
        .options(
            selectinload(Student.enrollments).selectinload(Enrollment.course),
            selectinload(Student.exams),
            selectinload(Student.payments),
        )
    )
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    if not student:
        return None

    return {
        "student": student,
        "enrollments": student.enrollments,
        "exams": student.exams,
        "payments": student.payments,
    }


async def list_students(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Student]:
    """List students with optional status filter."""
    stmt = select(Student).order_by(Student.created_at.desc()).limit(limit).offset(offset)
    if status:
        stmt = stmt.where(Student.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())
