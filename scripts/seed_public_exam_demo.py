import asyncio
from datetime import date, datetime, timezone

from sqlalchemy import select

from db import SessionLocal
from db.models import Course, Exam, ExamSubmission, Examinee


PHONE = "0527180504"
EXAM_SEED_TAG = "דמו"
COURSE_NAME = "קורס דמו — מבחני נדרים"
EXAM_NAMES = [
    f"מבחן {EXAM_SEED_TAG} 1",
    f"מבחן {EXAM_SEED_TAG} 2",
    f"מבחן {EXAM_SEED_TAG} 3",
]


async def _get_or_create_course(db) -> Course:
    res = await db.execute(select(Course).where(Course.name == COURSE_NAME))
    course = res.scalar_one_or_none()
    if course:
        return course

    course = Course(name=COURSE_NAME, is_active=True)
    db.add(course)
    await db.flush()
    return course


async def _get_or_create_examinee(db) -> Examinee:
    res = await db.execute(select(Examinee).where(Examinee.phone == PHONE))
    ex = res.scalar_one_or_none()
    if ex:
        return ex

    ex = Examinee(full_name="נבחן דמו", phone=PHONE, source="public_exam_demo")
    db.add(ex)
    await db.flush()
    return ex


async def _get_or_create_exam(db, *, course_id: int, name: str, exam_dt: date) -> Exam:
    res = await db.execute(select(Exam).where(Exam.course_id == course_id, Exam.name == name))
    row = res.scalar_one_or_none()
    if row:
        return row

    row = Exam(
        name=name,
        course_id=course_id,
        exam_date=exam_dt,
        exam_type="בכתב",
    )
    db.add(row)
    await db.flush()
    return row


async def _exam_exists(db, *, course_id: int, name: str) -> bool:
    res = await db.execute(select(Exam.id).where(Exam.course_id == course_id, Exam.name == name))
    return res.scalar_one_or_none() is not None


async def _ensure_submission(db, *, exam_id: int, examinee_id: int, score: int, status: str) -> bool:
    res = await db.execute(
        select(ExamSubmission).where(
            ExamSubmission.exam_id == exam_id,
            ExamSubmission.examinee_id == examinee_id,
        )
    )
    existing = res.scalar_one_or_none()
    if existing:
        return False

    sub = ExamSubmission(
        exam_id=exam_id,
        examinee_id=examinee_id,
        submitted_at=datetime.now(timezone.utc),
        score=score,
        status=status,
    )
    db.add(sub)
    await db.flush()
    return True


async def main() -> None:
    async with SessionLocal() as db:
        course = await _get_or_create_course(db)
        ex = await _get_or_create_examinee(db)

        created_exams = 0
        created_subs = 0

        today = date.today()
        exam_dates = [today, date.fromordinal(today.toordinal() - 14), date.fromordinal(today.toordinal() - 45)]
        scores = [92, 78, 64]
        statuses = ["עבר", "נבדק", "נכשל"]

        for i, name in enumerate(EXAM_NAMES):
            existed = await _exam_exists(db, course_id=course.id, name=name)
            exam = await _get_or_create_exam(db, course_id=course.id, name=name, exam_dt=exam_dates[i % len(exam_dates)])
            if not existed:
                created_exams += 1

            created = await _ensure_submission(
                db,
                exam_id=exam.id,
                examinee_id=ex.id,
                score=scores[i % len(scores)],
                status=statuses[i % len(statuses)],
            )
            if created:
                created_subs += 1

        await db.commit()

    print("Seed complete")
    print("phone:", PHONE)
    print("course:", COURSE_NAME)
    print("exams_target:", len(EXAM_NAMES))
    print("exams_created:", created_exams)
    print("submissions_created:", created_subs)


if __name__ == "__main__":
    asyncio.run(main())
