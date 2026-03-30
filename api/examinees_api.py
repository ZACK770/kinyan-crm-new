from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import examinees as examinee_svc
from services import audit_logs
from services.exam_registration import get_examinee_registrations as get_public_registrations
from .dependencies import require_entity_access, require_permission

router = APIRouter(tags=["examinees"])


class BulkUpdateRequest(BaseModel):
    ids: list[int]
    field: str
    value: str | int | float | bool | None = None


class BulkDeleteRequest(BaseModel):
    ids: list[int]


class ExamineeCreate(BaseModel):
    phone: str
    full_name: str | None = None
    id_number: str | None = None
    email: str | None = None
    source: str | None = None
    student_id: int | None = None


class RegisterForExamRequest(BaseModel):
    exam_id: int


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


@router.post("/")
async def create_examinee(
    data: ExamineeCreate,
    request: Request,
    user=Depends(require_entity_access("examinees", "create")),
    db: AsyncSession = Depends(get_db),
):
    try:
        ex = await examinee_svc.create_examinee(db, **data.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))

    await audit_logs.log_create(
        db=db,
        user=user,
        entity_type="examinees",
        entity_id=ex.id,
        description=f"נוצר נבחן חדש: {data.phone}",
        request=request,
    )
    await db.commit()
    return {"id": ex.id}


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


@router.delete("/{examinee_id}")
async def delete_examinee(
    examinee_id: int,
    request: Request,
    user=Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    deleted = await examinee_svc.delete_examinee(db, examinee_id)
    if deleted == 0:
        raise HTTPException(404, "Examinee not found")

    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="examinees",
        entity_id=examinee_id,
        description=f"נמחק נבחן #{examinee_id}",
        changes={"deleted_id": examinee_id},
        request=request,
    )
    await db.commit()
    return {"deleted": 1, "message": "נבחן נמחק בהצלחה"}


@router.get("/{examinee_id}/submissions")
async def list_examinee_submissions(
    examinee_id: int,
    user=Depends(require_entity_access("examinees", "view")),
    db: AsyncSession = Depends(get_db),
):
    # Ensure examinee exists (clear 404 instead of returning empty)
    ex = await examinee_svc.get_examinee(db, examinee_id)
    if not ex:
        raise HTTPException(404, "Examinee not found")
    return await examinee_svc.list_examinee_submissions(db, examinee_id)


@router.post("/{examinee_id}/registrations")
async def register_for_exam(
    examinee_id: int,
    data: RegisterForExamRequest,
    request: Request,
    user=Depends(require_entity_access("examinees", "edit")),
    db: AsyncSession = Depends(get_db),
):
    ex = await examinee_svc.get_examinee(db, examinee_id)
    if not ex:
        raise HTTPException(404, "Examinee not found")

    sub = await examinee_svc.register_examinee_for_exam(db, examinee_id=examinee_id, exam_id=data.exam_id)

    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="examinees",
        entity_id=examinee_id,
        description=f"רישום נבחן למבחן #{data.exam_id}",
        changes={"action": "register_for_exam", "exam_id": data.exam_id, "submission_id": sub.id},
        request=request,
    )
    await db.commit()
    return {"id": sub.id, "status": sub.status}


@router.get("/{examinee_id}/exam-registrations")
async def get_examinee_exam_registrations(
    examinee_id: int,
    user=Depends(require_entity_access("examinees", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get exam registrations from the new registration system"""
    ex = await examinee_svc.get_examinee(db, examinee_id)
    if not ex:
        raise HTTPException(404, "Examinee not found")
    
    # Get registrations from the new system
    registrations = await get_public_registrations(db, ex.phone)
    return registrations


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
