from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import examinees as examinee_svc
from services import audit_logs
from .dependencies import require_entity_access, require_permission

router = APIRouter(tags=["examinees"])


class BulkUpdateRequest(BaseModel):
    ids: list[int]
    field: str
    value: str | int | float | bool | None = None


class BulkDeleteRequest(BaseModel):
    ids: list[int]


@router.get("/")
async def list_examinees(
    search: str | None = Query(None),
    limit: int = Query(50, le=5000),
    offset: int = Query(0),
    user=Depends(require_entity_access("examinees", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await examinee_svc.list_examinees(db, search=search, limit=limit, offset=offset)
    return [
        {
            "id": e.id,
            "full_name": e.full_name,
            "phone": e.phone,
            "id_number": e.id_number,
            "email": e.email,
            "source": e.source,
            "student_id": e.student_id,
            "created_at": str(e.created_at) if getattr(e, "created_at", None) else None,
            "updated_at": str(e.updated_at) if getattr(e, "updated_at", None) else None,
        }
        for e in items
    ]


@router.get("/{examinee_id}")
async def get_examinee(
    examinee_id: int,
    user=Depends(require_entity_access("examinees", "view")),
    db: AsyncSession = Depends(get_db),
):
    ex = await examinee_svc.get_examinee(db, examinee_id)
    if not ex:
        raise HTTPException(404, "Examinee not found")
    return {
        "id": ex.id,
        "full_name": ex.full_name,
        "phone": ex.phone,
        "id_number": ex.id_number,
        "email": ex.email,
        "source": ex.source,
        "student_id": ex.student_id,
        "created_at": str(ex.created_at) if getattr(ex, "created_at", None) else None,
        "updated_at": str(ex.updated_at) if getattr(ex, "updated_at", None) else None,
    }


@router.patch("/{examinee_id}")
async def update_examinee(
    examinee_id: int,
    data: dict,
    request: Request,
    user=Depends(require_entity_access("examinees", "edit")),
    db: AsyncSession = Depends(get_db),
):
    ex = await examinee_svc.update_examinee(db, examinee_id, data)
    if not ex:
        raise HTTPException(404, "Examinee not found")

    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="examinees",
        entity_id=examinee_id,
        description="עדכון נבחן",
        changes=data,
        request=request,
    )

    await db.commit()
    return {"id": ex.id, "status": "updated", "updated_at": str(ex.updated_at) if getattr(ex, "updated_at", None) else None}


@router.post("/bulk-update")
async def bulk_update_examinees(
    data: BulkUpdateRequest,
    request: Request,
    user=Depends(require_entity_access("examinees", "edit")),
    db: AsyncSession = Depends(get_db),
):
    try:
        count = await examinee_svc.bulk_update_examinees(db, data.ids, data.field, data.value)
        await audit_logs.log_update(
            db=db,
            user=user,
            entity_type="examinees",
            entity_id=0,
            description=f"עדכון גורף: {data.field}={data.value} ל-{count} נבחנים",
            changes={"ids": data.ids, "field": data.field, "value": data.value},
            request=request,
        )
        await db.commit()
        return {"updated": count}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/bulk-delete")
async def bulk_delete_examinees(
    data: BulkDeleteRequest,
    request: Request,
    user=Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    count = await examinee_svc.bulk_delete_examinees(db, data.ids)
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="examinees",
        entity_id=0,
        description=f"מחיקה גורפת של {count} נבחנים",
        changes={"deleted_ids": data.ids},
        request=request,
    )
    await db.commit()
    return {"deleted": count}
