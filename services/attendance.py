"""
Attendance service.
Track student attendance and assignment completion per module.
"""
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Attendance


async def record_attendance(
    db: AsyncSession,
    student_id: int,
    module_id: int,
    is_present: bool = True,
    assignment_done: bool = False,
    score: int | None = None,
    lecturer_id: int | None = None,
    attendance_date: date | None = None,
) -> Attendance:
    """Record attendance for a student in a module session."""
    record = Attendance(
        student_id=student_id,
        module_id=module_id,
        lecturer_id=lecturer_id,
        attendance_date=attendance_date or date.today(),
        is_present=is_present,
        assignment_done=assignment_done,
        score=score,
    )
    db.add(record)
    await db.flush()
    return record


async def get_student_attendance(
    db: AsyncSession,
    student_id: int,
    course_id: int | None = None,
) -> list[Attendance]:
    """Get attendance records for a student, optionally filtered by course."""
    stmt = select(Attendance).where(Attendance.student_id == student_id).order_by(Attendance.attendance_date.desc())
    # If filtering by course, join through module
    if course_id:
        from db.models import CourseModule
        stmt = stmt.join(CourseModule).where(CourseModule.course_id == course_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_module_attendance_rate(db: AsyncSession, module_id: int) -> dict:
    """Calculate attendance rate for a module."""
    total_stmt = select(func.count()).select_from(Attendance).where(Attendance.module_id == module_id)
    present_stmt = total_stmt.where(Attendance.is_present == True)  # noqa: E712
    assignment_stmt = total_stmt.where(Attendance.assignment_done == True)  # noqa: E712

    total = (await db.execute(total_stmt)).scalar() or 0
    present = (await db.execute(present_stmt)).scalar() or 0
    assignments = (await db.execute(assignment_stmt)).scalar() or 0

    return {
        "total_records": total,
        "present": present,
        "attendance_rate": round(present / total * 100, 1) if total > 0 else 0,
        "assignment_rate": round(assignments / total * 100, 1) if total > 0 else 0,
    }
