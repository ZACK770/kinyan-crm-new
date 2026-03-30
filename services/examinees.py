from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Examinee, ExamSubmission, Exam
from utils.phone import normalize_phone


async def list_examinees(
    db: AsyncSession,
    *,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Examinee]:
    stmt = select(Examinee)

    if search:
        q = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Examinee.phone.ilike(q),
                Examinee.full_name.ilike(q),
                Examinee.id_number.ilike(q),
                Examinee.email.ilike(q),
            )
        )

    stmt = stmt.order_by(Examinee.id.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def create_examinee(
    db: AsyncSession,
    *,
    phone: str,
    full_name: str | None = None,
    id_number: str | None = None,
    email: str | None = None,
    source: str | None = None,
    student_id: int | None = None,
) -> Examinee:
    clean_phone = normalize_phone(phone)
    if not clean_phone:
        raise ValueError("טלפון לא תקין")

    ex = Examinee(
        phone=clean_phone,
        full_name=full_name,
        id_number=id_number,
        email=email,
        source=source or "external_exam_product",
        student_id=student_id,
    )
    db.add(ex)
    await db.flush()
    return ex


async def get_examinee(db: AsyncSession, examinee_id: int) -> Examinee | None:
    stmt = select(Examinee).where(Examinee.id == examinee_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def update_examinee(db: AsyncSession, examinee_id: int, data: dict) -> Examinee | None:
    ex = await get_examinee(db, examinee_id)
    if not ex:
        return None

    allowed = {
        "full_name",
        "phone",
        "id_number",
        "email",
        "source",
        "student_id",
    }

    for k, v in data.items():
        if k in allowed:
            if k == "phone" and v is not None:
                clean_phone = normalize_phone(str(v))
                if not clean_phone:
                    raise ValueError("טלפון לא תקין")
                setattr(ex, k, clean_phone)
                continue
            setattr(ex, k, v)

    await db.flush()
    return ex


async def delete_examinee(db: AsyncSession, examinee_id: int) -> int:
    from sqlalchemy import delete as sa_delete

    result = await db.execute(sa_delete(Examinee).where(Examinee.id == examinee_id))
    await db.flush()
    return result.rowcount or 0


async def list_examinee_submissions(db: AsyncSession, examinee_id: int) -> list[dict]:
    stmt = (
        select(ExamSubmission, Exam)
        .join(Exam, Exam.id == ExamSubmission.exam_id)
        .where(ExamSubmission.examinee_id == examinee_id)
        .order_by(ExamSubmission.id.desc())
    )
    res = await db.execute(stmt)
    rows = res.all()
    items: list[dict] = []
    for sub, exam in rows:
        items.append(
            {
                "id": sub.id,
                "exam_id": sub.exam_id,
                "exam_name": exam.name,
                "exam_date": str(exam.exam_date) if exam.exam_date else None,
                "exam_type": exam.exam_type,
                "submitted_at": str(sub.submitted_at) if sub.submitted_at else None,
                "score": sub.score,
                "status": sub.status,
                "student_notes": sub.student_notes,
                "internal_notes": sub.internal_notes,
            }
        )
    return items


async def register_examinee_for_exam(
    db: AsyncSession,
    *,
    examinee_id: int,
    exam_id: int,
) -> ExamSubmission:
    # Ensure no duplicate registration
    stmt = select(ExamSubmission).where(
        ExamSubmission.examinee_id == examinee_id,
        ExamSubmission.exam_id == exam_id,
    ).limit(1)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        return existing

    submission = ExamSubmission(
        exam_id=exam_id,
        examinee_id=examinee_id,
        student_id=None,
        submitted_at=None,
        score=None,
        status="נרשם",
        student_notes=None,
        internal_notes=None,
    )
    db.add(submission)
    await db.flush()
    return submission


async def bulk_update_examinees(db: AsyncSession, ids: list[int], field: str, value):
    if not ids:
        return 0
    allowed = {
        "full_name",
        "phone",
        "id_number",
        "email",
        "source",
        "student_id",
    }
    if field not in allowed:
        raise ValueError(f"Field not allowed: {field}")

    stmt = select(Examinee).where(Examinee.id.in_(ids))
    res = await db.execute(stmt)
    items = list(res.scalars().all())
    for ex in items:
        setattr(ex, field, value)
    await db.flush()
    return len(items)


async def bulk_delete_examinees(db: AsyncSession, ids: list[int]) -> int:
    from sqlalchemy import delete as sa_delete

    if not ids:
        return 0
    result = await db.execute(sa_delete(Examinee).where(Examinee.id.in_(ids)))
    await db.flush()
    return result.rowcount or 0
