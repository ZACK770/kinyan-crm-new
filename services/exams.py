"""
Exams service.
Manage exams and student submissions.
"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Exam, ExamSubmission


async def create_exam(
    db: AsyncSession,
    name: str,
    course_id: int,
    exam_type: str = "בכתב",
    lecturer_id: int | None = None,
    exam_date=None,
    questionnaire_url: str | None = None,
    answers_url: str | None = None,
) -> Exam:
    """Create a new exam."""
    exam = Exam(
        name=name,
        course_id=course_id,
        exam_type=exam_type,
        lecturer_id=lecturer_id,
        exam_date=exam_date,
        questionnaire_url=questionnaire_url,
        answers_url=answers_url,
    )
    db.add(exam)
    await db.flush()
    return exam


async def add_submission(
    db: AsyncSession,
    exam_id: int,
    student_id: int,
    score: int | None = None,
    status: str = "הוגש",
    student_notes: str | None = None,
    internal_notes: str | None = None,
) -> ExamSubmission:
    """Add a student submission to an exam."""
    submission = ExamSubmission(
        exam_id=exam_id,
        student_id=student_id,
        submitted_at=func.now(),
        score=score,
        status=status,
        student_notes=student_notes,
        internal_notes=internal_notes,
    )
    db.add(submission)
    await db.flush()
    return submission


async def grade_submission(
    db: AsyncSession,
    submission_id: int,
    score: int,
    status: str = "נבדק",
    internal_notes: str | None = None,
) -> ExamSubmission | None:
    """Grade a submission."""
    stmt = select(ExamSubmission).where(ExamSubmission.id == submission_id)
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub:
        return None

    sub.score = score
    sub.status = status
    if internal_notes:
        sub.internal_notes = internal_notes
    await db.flush()
    return sub


async def get_exam_with_submissions(db: AsyncSession, exam_id: int) -> Exam | None:
    """Get exam with all submissions."""
    stmt = (
        select(Exam)
        .where(Exam.id == exam_id)
        .options(selectinload(Exam.submissions))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_exam_average(db: AsyncSession, exam_id: int) -> float | None:
    """Calculate average score for an exam."""
    stmt = select(func.avg(ExamSubmission.score)).where(
        ExamSubmission.exam_id == exam_id,
        ExamSubmission.score.isnot(None),
    )
    result = await db.execute(stmt)
    avg = result.scalar()
    return round(float(avg), 1) if avg else None


async def list_course_exams(db: AsyncSession, course_id: int) -> list[Exam]:
    """Get all exams for a course."""
    stmt = select(Exam).where(Exam.course_id == course_id).order_by(Exam.exam_date.desc().nullslast())
    result = await db.execute(stmt)
    return list(result.scalars().all())
