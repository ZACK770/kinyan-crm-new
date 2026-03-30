"""
Exams service.
Manage exams and student submissions.
"""
from datetime import datetime
from datetime import date

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Exam, ExamSubmission, ExamDate, ExamDateExam


async def create_exam(
    db: AsyncSession,
    name: str,
    course_id: int,
    exam_type: str = "בכתב",
    lecturer_id: int | None = None,
    exam_date=None,
    questionnaire_url: str | None = None,
    answers_url: str | None = None,
    material: str | None = None,
    registration_price: int | None = None,
    registration_url: str | None = None,
    is_registration_open: bool | None = None,
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
        material=material,
        registration_price=registration_price,
        registration_url=registration_url,
        is_registration_open=is_registration_open if is_registration_open is not None else True,
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


async def list_exams(db: AsyncSession, limit: int = 200, course_id: int | None = None) -> list[Exam]:
    stmt = select(Exam)
    if course_id is not None:
        stmt = stmt.where(Exam.course_id == course_id)
    stmt = stmt.order_by(Exam.exam_date.desc().nullslast(), Exam.id.desc()).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_exam(db: AsyncSession, exam_id: int) -> Exam | None:
    res = await db.execute(select(Exam).where(Exam.id == exam_id))
    return res.scalar_one_or_none()


async def update_exam(
    db: AsyncSession,
    exam_id: int,
    *,
    name: str | None = None,
    course_id: int | None = None,
    exam_type: str | None = None,
    lecturer_id: int | None = None,
    exam_date: date | None = None,
    questionnaire_url: str | None = None,
    answers_url: str | None = None,
    material: str | None = None,
    registration_price: int | None = None,
    registration_url: str | None = None,
    is_registration_open: bool | None = None,
) -> Exam | None:
    exam = await get_exam(db, exam_id)
    if not exam:
        return None

    if name is not None:
        exam.name = name
    if course_id is not None:
        exam.course_id = course_id
    if exam_type is not None:
        exam.exam_type = exam_type
    if lecturer_id is not None:
        exam.lecturer_id = lecturer_id
    if exam_date is not None:
        exam.exam_date = exam_date
    if questionnaire_url is not None:
        exam.questionnaire_url = questionnaire_url
    if answers_url is not None:
        exam.answers_url = answers_url
    if material is not None:
        exam.material = material
    if registration_price is not None:
        exam.registration_price = registration_price
    if registration_url is not None:
        exam.registration_url = registration_url
    if is_registration_open is not None:
        exam.is_registration_open = is_registration_open

    await db.flush()
    return exam


async def delete_exam(db: AsyncSession, exam_id: int) -> bool:
    exam = await get_exam(db, exam_id)
    if not exam:
        return False

    # Guard: cannot delete if there are submissions or registrations via exam_date_exams.
    sub_count = await db.scalar(select(func.count(ExamSubmission.id)).where(ExamSubmission.exam_id == exam_id))
    if sub_count and int(sub_count) > 0:
        raise ValueError("לא ניתן למחוק מבחן עם הגשות")

    await db.execute(delete(ExamDateExam).where(ExamDateExam.exam_id == exam_id))
    await db.delete(exam)
    await db.flush()
    return True


async def list_exam_dates(db: AsyncSession, limit: int = 500) -> list[ExamDate]:
    stmt = select(ExamDate).order_by(ExamDate.date.desc(), ExamDate.id.desc()).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_exam_date(db: AsyncSession, exam_date_id: int) -> ExamDate | None:
    stmt = select(ExamDate).where(ExamDate.id == exam_date_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def create_exam_date(
    db: AsyncSession,
    *,
    date_value: date,
    description: str | None = None,
    is_active: bool = True,
    max_registrations: int | None = None,
) -> ExamDate:
    ed = ExamDate(
        date=date_value,
        description=description,
        is_active=is_active,
        max_registrations=max_registrations,
    )
    db.add(ed)
    await db.flush()
    return ed


async def update_exam_date(
    db: AsyncSession,
    exam_date_id: int,
    *,
    date_value: date | None = None,
    description: str | None = None,
    is_active: bool | None = None,
    max_registrations: int | None = None,
) -> ExamDate | None:
    ed = await get_exam_date(db, exam_date_id)
    if not ed:
        return None
    if date_value is not None:
        ed.date = date_value
    if description is not None:
        ed.description = description
    if is_active is not None:
        ed.is_active = is_active
    if max_registrations is not None:
        ed.max_registrations = max_registrations
    await db.flush()
    return ed


async def delete_exam_date(db: AsyncSession, exam_date_id: int) -> bool:
    ed = await get_exam_date(db, exam_date_id)
    if not ed:
        return False
    await db.execute(delete(ExamDateExam).where(ExamDateExam.exam_date_id == exam_date_id))
    await db.delete(ed)
    await db.flush()
    return True


async def list_exam_date_exams(db: AsyncSession, exam_date_id: int) -> list[Exam]:
    stmt = (
        select(Exam)
        .join(ExamDateExam, ExamDateExam.exam_id == Exam.id)
        .where(ExamDateExam.exam_date_id == exam_date_id)
        .order_by(Exam.id.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def assign_exam_to_date(db: AsyncSession, exam_date_id: int, exam_id: int) -> None:
    existing = await db.scalar(
        select(func.count(ExamDateExam.exam_id)).where(
            (ExamDateExam.exam_date_id == exam_date_id) & (ExamDateExam.exam_id == exam_id)
        )
    )
    if existing and int(existing) > 0:
        return
    db.add(ExamDateExam(exam_date_id=exam_date_id, exam_id=exam_id))
    await db.flush()


async def unassign_exam_from_date(db: AsyncSession, exam_date_id: int, exam_id: int) -> None:
    await db.execute(
        delete(ExamDateExam).where(
            (ExamDateExam.exam_date_id == exam_date_id) & (ExamDateExam.exam_id == exam_id)
        )
    )
    await db.flush()
