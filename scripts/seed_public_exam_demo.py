import asyncio
import os
from datetime import date, datetime, timezone

import asyncpg


PHONE = "0527180504"
EXAM_SEED_TAG = "דמו"
COURSE_NAME = "קורס דמו — מבחני נדרים"
EXAM_NAMES = [
    f"מבחן {EXAM_SEED_TAG} 1",
    f"מבחן {EXAM_SEED_TAG} 2",
    f"מבחן {EXAM_SEED_TAG} 3",
]

def _pg_url_from_env() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


async def _get_or_create_course(conn) -> int:
    course_id = await conn.fetchval("select id from courses where name=$1", COURSE_NAME)
    if course_id:
        return int(course_id)

    course_id = await conn.fetchval(
        """
        insert into courses (name, is_active, payments_count)
        values ($1, true, 1)
        returning id
        """,
        COURSE_NAME,
    )
    return int(course_id)


async def _get_or_create_examinee(conn) -> int:
    ex_id = await conn.fetchval("select id from examinees where phone=$1", PHONE)
    if ex_id:
        return int(ex_id)

    ex_id = await conn.fetchval(
        """
        insert into examinees (full_name, phone, source)
        values ($1, $2, $3)
        returning id
        """,
        "נבחן דמו",
        PHONE,
        "public_exam_demo",
    )
    return int(ex_id)


async def _get_or_create_exam(conn, *, course_id: int, name: str, exam_dt: date) -> tuple[int, bool]:
    exam_id = await conn.fetchval("select id from exams where course_id=$1 and name=$2", course_id, name)
    if exam_id:
        return int(exam_id), False

    exam_id = await conn.fetchval(
        """
        insert into exams (name, course_id, exam_date, exam_type)
        values ($1, $2, $3, $4)
        returning id
        """,
        name,
        course_id,
        exam_dt,
        "בכתב",
    )
    return int(exam_id), True


async def _ensure_submission(
    conn,
    *,
    exam_id: int,
    examinee_id: int,
    score: int,
    status: str,
) -> bool:
    exists = await conn.fetchval(
        """
        select 1
        from exam_submissions
        where exam_id=$1 and examinee_id=$2
        """,
        exam_id,
        examinee_id,
    )
    if exists:
        return False

    await conn.execute(
        """
        insert into exam_submissions (exam_id, examinee_id, submitted_at, score, status)
        values ($1, $2, $3, $4, $5)
        """,
        exam_id,
        examinee_id,
        datetime.now(timezone.utc),
        score,
        status,
    )
    return True


async def main() -> None:
    url = _pg_url_from_env()
    conn = await asyncpg.connect(url, ssl="require")
    try:
        async with conn.transaction():
            course_id = await _get_or_create_course(conn)
            examinee_id = await _get_or_create_examinee(conn)

            created_exams = 0
            created_subs = 0

            today = date.today()
            exam_dates = [today, date.fromordinal(today.toordinal() - 14), date.fromordinal(today.toordinal() - 45)]
            scores = [92, 78, 64]
            statuses = ["עבר", "נבדק", "נכשל"]

            for i, name in enumerate(EXAM_NAMES):
                exam_id, created_exam = await _get_or_create_exam(
                    conn,
                    course_id=course_id,
                    name=name,
                    exam_dt=exam_dates[i % len(exam_dates)],
                )
                if created_exam:
                    created_exams += 1

                created_sub = await _ensure_submission(
                    conn,
                    exam_id=exam_id,
                    examinee_id=examinee_id,
                    score=scores[i % len(scores)],
                    status=statuses[i % len(statuses)],
                )
                if created_sub:
                    created_subs += 1
    finally:
        await conn.close()

    print("Seed complete")
    print("phone:", PHONE)
    print("course:", COURSE_NAME)
    print("exams_target:", len(EXAM_NAMES))
    print("exams_created:", created_exams)
    print("submissions_created:", created_subs)


if __name__ == "__main__":
    asyncio.run(main())
