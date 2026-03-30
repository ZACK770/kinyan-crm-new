from sqlalchemy import select, or_, false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Examinee, Exam, ExamSubmission, Student


async def get_exam_results_by_phone(db: AsyncSession, phone: str) -> list[dict]:
    """Returns a list of exam results for Nedarim public display."""

    examinee_ids: list[int] = []
    student_ids: list[int] = []

    ex_stmt = select(Examinee.id).where(Examinee.phone == phone)
    ex_res = await db.execute(ex_stmt)
    examinee_ids = list(ex_res.scalars().all())

    st_stmt = select(Student.id).where(Student.phone == phone)
    st_res = await db.execute(st_stmt)
    student_ids = list(st_res.scalars().all())

    if not examinee_ids and not student_ids:
        return []

    conditions = []
    if student_ids:
        conditions.append(ExamSubmission.student_id.in_(student_ids))
    if examinee_ids:
        conditions.append(ExamSubmission.examinee_id.in_(examinee_ids))

    sub_stmt = (
        select(ExamSubmission)
        .options(selectinload(ExamSubmission.exam).selectinload(Exam.course))
        .where(or_(*conditions) if conditions else false())
    )
    sub_res = await db.execute(sub_stmt)
    subs = list(sub_res.scalars().all())

    items: list[dict] = []
    for s in subs:
        exam = s.exam
        course = getattr(exam, "course", None)
        items.append(
            {
                "exam_id": exam.id,
                "exam_name": exam.name,
                "exam_type": exam.exam_type,
                "exam_date": str(exam.exam_date) if exam.exam_date else None,
                "course_id": exam.course_id,
                "course_name": getattr(course, "name", None) if course else None,
                "score": s.score,
                "status": s.status,
                "submitted_at": str(s.submitted_at) if s.submitted_at else None,
            }
        )

    items.sort(key=lambda x: (x["exam_date"] is None, x["exam_date"] or ""), reverse=True)
    return items
