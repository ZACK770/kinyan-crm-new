from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Examinee


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
            setattr(ex, k, v)

    await db.flush()
    return ex


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
