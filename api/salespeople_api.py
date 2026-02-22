"""
Salespeople management API endpoints.
CRUD for salespeople + statistics.
Prefix: /api/salespeople
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import Salesperson
from services import sales as sales_svc
from services import audit_logs
from .dependencies import require_entity_access

router = APIRouter(tags=["salespeople"])


# ── Schemas ────────────────────────────────────────
class SalespersonCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    ref_code: Optional[str] = None
    notes: Optional[str] = None
    notification_webhook_url: Optional[str] = None


class SalespersonUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    ref_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    notification_webhook_url: Optional[str] = None
    notify_on_new_lead: Optional[bool] = None


def _sp_to_dict(sp: Salesperson, stats: dict | None = None) -> dict:
    """Convert Salesperson model to API response dict."""
    d = {
        "id": sp.id,
        "user_id": sp.user_id,
        "name": sp.name,
        "phone": sp.phone,
        "email": sp.email,
        "ref_code": sp.ref_code,
        "notes": sp.notes,
        "is_active": sp.is_active,
        "notification_webhook_url": sp.notification_webhook_url,
        "notify_on_new_lead": sp.notify_on_new_lead,
        "created_at": str(sp.created_at) if sp.created_at else None,
    }
    if stats:
        d.update(stats)
    return d


# ── Endpoints ────────────────────────────────────────
@router.get("/")
async def list_salespeople(
    user=Depends(require_entity_access("salespeople", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get all salespeople with lead statistics."""
    salespeople = await sales_svc.get_all_salespeople(db)
    result = []
    for sp in salespeople:
        stats = await sales_svc.get_salesperson_stats(db, sp.id)
        result.append(_sp_to_dict(sp, stats))
    return result


@router.get("/{sp_id}")
async def get_salesperson(
    sp_id: int,
    user=Depends(require_entity_access("salespeople", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single salesperson with full details."""
    sp = await sales_svc.get_salesperson_by_id(db, sp_id)
    if not sp:
        raise HTTPException(404, "איש מכירות לא נמצא")
    stats = await sales_svc.get_salesperson_stats(db, sp.id)
    return _sp_to_dict(sp, stats)


@router.post("/")
async def create_salesperson(
    data: SalespersonCreate,
    request: Request,
    user=Depends(require_entity_access("salespeople", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new salesperson (manual, not linked to a user)."""
    sp = await sales_svc.create_salesperson(
        db,
        name=data.name,
        phone=data.phone,
        email=data.email,
        ref_code=data.ref_code,
        notes=data.notes,
        notification_webhook_url=data.notification_webhook_url,
    )
    await audit_logs.log_create(
        db=db, user=user, entity_type="salespeople", entity_id=sp.id,
        description=f"נוצר איש מכירות: {sp.name}", request=request,
    )
    await db.commit()
    return _sp_to_dict(sp)


@router.patch("/{sp_id}")
async def update_salesperson(
    sp_id: int,
    data: SalespersonUpdate,
    request: Request,
    user=Depends(require_entity_access("salespeople", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Update salesperson details."""
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, "אין שדות לעדכון")

    sp = await sales_svc.update_salesperson(db, sp_id, **update_data)
    if not sp:
        raise HTTPException(404, "איש מכירות לא נמצא")

    await audit_logs.log_update(
        db=db, user=user, entity_type="salespeople", entity_id=sp_id,
        description=f"עודכן איש מכירות: {sp.name}",
        changes=update_data, request=request,
    )
    await db.commit()
    stats = await sales_svc.get_salesperson_stats(db, sp.id)
    return _sp_to_dict(sp, stats)


@router.delete("/{sp_id}")
async def deactivate_salesperson(
    sp_id: int,
    request: Request,
    user=Depends(require_entity_access("salespeople", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete: deactivate a salesperson (keeps leads intact)."""
    sp = await sales_svc.get_salesperson_by_id(db, sp_id)
    if not sp:
        raise HTTPException(404, "איש מכירות לא נמצא")
    sp.is_active = False
    await audit_logs.log_delete(
        db=db, user=user, entity_type="salespeople", entity_id=sp_id,
        description=f"הושבת איש מכירות: {sp.name}", request=request,
    )
    await db.commit()
    return {"success": True, "message": f"איש מכירות {sp.name} הושבת"}
