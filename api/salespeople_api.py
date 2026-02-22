"""
Salespeople management API endpoints.
CRUD for salespeople + statistics + assignment rules.
Prefix: /api/salespeople
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import Salesperson, Lead, LeadInteraction, SalesAssignmentRules, SalesTask, Payment
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


class AssignmentRulesUpsert(BaseModel):
    daily_lead_limit: int | None = Field(None, ge=0)
    priority_weight: int = Field(5, ge=1, le=10)
    max_open_leads: int | None = Field(None, ge=0)
    is_active: bool = True


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


# ── Detailed Stats ────────────────────────────────────────
@router.get("/{sp_id}/detailed-stats")
async def get_salesperson_detailed_stats(
    sp_id: int,
    days: int = Query(30, ge=1, le=365),
    user=Depends(require_entity_access("salespeople", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed stats for a salesperson: status breakdown, conversions, interactions, trends."""
    sp = await sales_svc.get_salesperson_by_id(db, sp_id)
    if not sp:
        raise HTTPException(404, "איש מכירות לא נמצא")

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    # Status distribution for this salesperson's leads in period
    status_rows = (await db.execute(
        select(Lead.status, func.count(Lead.id).label("count"))
        .where(Lead.salesperson_id == sp_id)
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .group_by(Lead.status)
        .order_by(func.count(Lead.id).desc())
    )).all()
    status_distribution = [{"name": r.status or "לא מוגדר", "value": r.count} for r in status_rows]

    # Lead trends (daily)
    trend_rows = (await db.execute(
        select(
            cast(Lead.created_at, Date).label("day"),
            func.count(Lead.id).label("leads"),
        )
        .where(Lead.salesperson_id == sp_id)
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .group_by(cast(Lead.created_at, Date))
        .order_by(cast(Lead.created_at, Date))
    )).all()
    lead_trends = [{"date": str(r.day), "leads": r.leads} for r in trend_rows]

    # Conversion stats
    total_in_period = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.salesperson_id == sp_id)
        .where(Lead.created_at >= start, Lead.created_at <= end)
    )).scalar() or 0

    converted_in_period = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.salesperson_id == sp_id)
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .where(Lead.status.in_(["נסלק", "תלמיד פעיל", "converted", "ליד סגור - לקוח"]))
    )).scalar() or 0

    conversion_rate = round((converted_in_period / total_in_period * 100), 1) if total_in_period > 0 else 0

    # Interactions count
    interactions_count = (await db.execute(
        select(func.count(LeadInteraction.id))
        .join(Lead, Lead.id == LeadInteraction.lead_id)
        .where(Lead.salesperson_id == sp_id)
        .where(LeadInteraction.created_at >= start, LeadInteraction.created_at <= end)
    )).scalar() or 0

    # Open tasks
    open_tasks = (await db.execute(
        select(func.count(SalesTask.id))
        .where(SalesTask.salesperson_id == sp_id)
        .where(SalesTask.status != "הושלם")
    )).scalar() or 0

    # New leads in period
    new_leads = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.salesperson_id == sp_id)
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .where(Lead.status == "ליד חדש")
    )).scalar() or 0

    # In-progress leads
    in_progress = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.salesperson_id == sp_id)
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .where(Lead.status.in_(["ליד בתהליך", "חיוג ראשון"]))
    )).scalar() or 0

    # Revenue from this salesperson's leads
    revenue = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .join(Lead, Lead.id == Payment.lead_id)
        .where(Lead.salesperson_id == sp_id)
        .where(Payment.status == "שולם")
        .where(Payment.created_at >= start, Payment.created_at <= end)
    )).scalar() or 0

    return {
        "period": {"from": str(start.date()), "to": str(end.date()), "days": days},
        "kpis": {
            "total_leads": total_in_period,
            "new_leads": new_leads,
            "in_progress": in_progress,
            "converted": converted_in_period,
            "conversion_rate": conversion_rate,
            "interactions": interactions_count,
            "open_tasks": open_tasks,
            "revenue": float(revenue),
        },
        "status_distribution": status_distribution,
        "lead_trends": lead_trends,
    }


# ── Assignment Rules per Salesperson ────────────────────────────────────────
@router.get("/{sp_id}/rules")
async def get_salesperson_rules(
    sp_id: int,
    user=Depends(require_entity_access("salespeople", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get assignment rules for a specific salesperson."""
    sp = await sales_svc.get_salesperson_by_id(db, sp_id)
    if not sp:
        raise HTTPException(404, "איש מכירות לא נמצא")

    result = await db.execute(
        select(SalesAssignmentRules).where(SalesAssignmentRules.salesperson_id == sp_id)
    )
    rules = result.scalar_one_or_none()

    if not rules:
        return {"has_rules": False, "rules": None}

    # Count current open leads
    open_statuses = rules.status_filters or ["ליד חדש", "במעקב", "מתעניין"]
    open_count = (await db.execute(
        select(func.count(Lead.id))
        .where(Lead.salesperson_id == sp_id)
        .where(Lead.status.in_(open_statuses))
    )).scalar() or 0

    return {
        "has_rules": True,
        "rules": {
            "id": rules.id,
            "daily_lead_limit": rules.daily_lead_limit,
            "daily_leads_assigned": rules.daily_leads_assigned,
            "last_reset_date": str(rules.last_reset_date) if rules.last_reset_date else None,
            "priority_weight": rules.priority_weight,
            "max_open_leads": rules.max_open_leads,
            "status_filters": rules.status_filters,
            "is_active": rules.is_active,
            "current_open_leads": open_count,
        },
    }


@router.put("/{sp_id}/rules")
async def upsert_salesperson_rules(
    sp_id: int,
    data: AssignmentRulesUpsert,
    request: Request,
    user=Depends(require_entity_access("salespeople", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Create or update assignment rules for a salesperson."""
    sp = await sales_svc.get_salesperson_by_id(db, sp_id)
    if not sp:
        raise HTTPException(404, "איש מכירות לא נמצא")

    result = await db.execute(
        select(SalesAssignmentRules).where(SalesAssignmentRules.salesperson_id == sp_id)
    )
    rules = result.scalar_one_or_none()

    if rules:
        rules.daily_lead_limit = data.daily_lead_limit
        rules.priority_weight = data.priority_weight
        rules.max_open_leads = data.max_open_leads
        rules.is_active = data.is_active
        action = "עודכנו"
    else:
        rules = SalesAssignmentRules(
            salesperson_id=sp_id,
            daily_lead_limit=data.daily_lead_limit,
            priority_weight=data.priority_weight,
            max_open_leads=data.max_open_leads,
            is_active=data.is_active,
        )
        db.add(rules)
        action = "נוצרו"

    await audit_logs.log_update(
        db=db, user=user, entity_type="salespeople", entity_id=sp_id,
        description=f"{action} כללי שיוך עבור: {sp.name}",
        changes=data.model_dump(), request=request,
    )
    await db.commit()
    return {"success": True, "message": f"כללי שיוך {action} בהצלחה"}
