"""
Dashboard API endpoints.
Provides overview stats, salesperson performance, conversion funnels,
lead trends, and source analytics for the dashboard widgets.
"""
import logging
from datetime import datetime, timedelta, timezone, date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, cast, Date, extract
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import Lead, Student, Enrollment, Payment, Salesperson, LeadInteraction, SalesTask
from services import sales as sales_svc
from .dependencies import require_permission

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])


def _parse_date_range(days: int = 30, from_date: str | None = None, to_date: str | None = None):
    """Parse date range from query params. Returns (start, end) as datetime."""
    if from_date and to_date:
        start = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    else:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
    return start, end


@router.get("/overview")
async def overview(
    user = Depends(require_permission("viewer")),
    db: AsyncSession = Depends(get_db)
):
    """System-wide dashboard stats."""
    total_leads = (await db.execute(select(func.count()).select_from(Lead))).scalar() or 0
    new_leads = (
        await db.execute(select(func.count()).select_from(Lead).where(Lead.status == "ליד חדש"))
    ).scalar() or 0
    total_students = (await db.execute(select(func.count()).select_from(Student))).scalar() or 0
    active_enrollments = (
        await db.execute(
            select(func.count()).select_from(Enrollment).where(Enrollment.status == "פעיל")
        )
    ).scalar() or 0
    total_revenue = (
        await db.execute(
            select(func.sum(Payment.amount)).where(Payment.status == "שולם")
        )
    ).scalar() or 0

    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "total_students": total_students,
        "active_enrollments": active_enrollments,
        "total_revenue": float(total_revenue),
    }


@router.get("/salespeople")
async def salespeople_stats(
    user = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db)
):
    """Per-salesperson stats."""
    people = await sales_svc.get_active_salespeople(db)
    result = []
    for sp in people:
        dashboard = await sales_svc.get_salesperson_dashboard(db, sp.id)
        result.append({
            "id": sp.id,
            "name": sp.name,
            "total_leads": dashboard["total_leads"],
            "new_leads": dashboard["new_leads"],
            "open_tasks": len(dashboard["open_tasks"]),
        })
    return result


@router.get("/advanced")
async def advanced_dashboard(
    days: int = Query(30, ge=1, le=365),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    user = Depends(require_permission("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """
    Advanced dashboard data with date range filtering.
    Returns: KPIs, status distribution, conversion funnel,
    lead trends, source breakdown, salesperson performance.
    """
    start, end = _parse_date_range(days, from_date, to_date)

    # ── KPI Cards ──
    total_leads_period = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.created_at >= start, Lead.created_at <= end)
    )).scalar() or 0

    converted_period = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .where(Lead.status == "converted")
    )).scalar() or 0

    total_interactions_period = (await db.execute(
        select(func.count()).select_from(LeadInteraction)
        .where(LeadInteraction.created_at >= start, LeadInteraction.created_at <= end)
    )).scalar() or 0

    revenue_period = (await db.execute(
        select(func.sum(Payment.amount))
        .where(Payment.status == "שולם")
        .where(Payment.created_at >= start, Payment.created_at <= end)
    )).scalar() or 0

    # Previous period for comparison
    period_length = (end - start).days
    prev_start = start - timedelta(days=period_length)
    prev_end = start

    prev_leads = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.created_at >= prev_start, Lead.created_at < prev_end)
    )).scalar() or 0

    prev_converted = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.created_at >= prev_start, Lead.created_at < prev_end)
        .where(Lead.status == "converted")
    )).scalar() or 0

    prev_revenue = (await db.execute(
        select(func.sum(Payment.amount))
        .where(Payment.status == "שולם")
        .where(Payment.created_at >= prev_start, Payment.created_at < prev_end)
    )).scalar() or 0

    conversion_rate = round((converted_period / total_leads_period * 100), 1) if total_leads_period > 0 else 0
    prev_conversion_rate = round((prev_converted / prev_leads * 100), 1) if prev_leads > 0 else 0

    kpis = {
        "total_leads": total_leads_period,
        "prev_leads": prev_leads,
        "converted": converted_period,
        "prev_converted": prev_converted,
        "conversion_rate": conversion_rate,
        "prev_conversion_rate": prev_conversion_rate,
        "total_interactions": total_interactions_period,
        "revenue": float(revenue_period),
        "prev_revenue": float(prev_revenue or 0),
    }

    # ── Status Distribution (Pie/Donut) ──
    status_rows = (await db.execute(
        select(Lead.status, func.count(Lead.id).label("count"))
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .group_by(Lead.status)
        .order_by(func.count(Lead.id).desc())
    )).all()
    status_distribution = [{"name": r.status or "לא מוגדר", "value": r.count} for r in status_rows]

    # ── Lead Trends (Line chart - daily/weekly) ──
    # Group by date
    lead_trend_rows = (await db.execute(
        select(
            cast(Lead.created_at, Date).label("day"),
            func.count(Lead.id).label("leads"),
        )
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .group_by(cast(Lead.created_at, Date))
        .order_by(cast(Lead.created_at, Date))
    )).all()
    lead_trends = [{"date": str(r.day), "leads": r.leads} for r in lead_trend_rows]

    # ── Conversion Funnel ──
    all_in_period = total_leads_period
    contacted = (await db.execute(
        select(func.count(func.distinct(LeadInteraction.lead_id)))
        .where(LeadInteraction.created_at >= start, LeadInteraction.created_at <= end)
    )).scalar() or 0

    interested = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .where(Lead.status.in_(["ליד בתהליך", "חיוג ראשון", "נסלק", "תלמיד פעיל", "converted"]))
    )).scalar() or 0

    paid = (await db.execute(
        select(func.count()).select_from(Lead)
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .where(Lead.payment_completed == True)
    )).scalar() or 0

    funnel = [
        {"stage": "לידים נכנסים", "value": all_in_period},
        {"stage": "נוצר קשר", "value": contacted},
        {"stage": "מתעניינים", "value": interested},
        {"stage": "שילמו", "value": paid},
        {"stage": "הומרו", "value": converted_period},
    ]

    # ── Source Breakdown (Bar chart) ──
    source_rows = (await db.execute(
        select(
            func.coalesce(Lead.source_type, "לא ידוע").label("source"),
            func.count(Lead.id).label("count"),
        )
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .group_by(Lead.source_type)
        .order_by(func.count(Lead.id).desc())
        .limit(10)
    )).all()
    source_breakdown = [{"source": r.source, "count": r.count} for r in source_rows]

    # ── Interaction Types (Donut) ──
    interaction_rows = (await db.execute(
        select(
            LeadInteraction.interaction_type,
            func.count(LeadInteraction.id).label("count"),
        )
        .where(LeadInteraction.created_at >= start, LeadInteraction.created_at <= end)
        .group_by(LeadInteraction.interaction_type)
        .order_by(func.count(LeadInteraction.id).desc())
    )).all()
    interaction_types = [{"type": r.interaction_type or "אחר", "count": r.count} for r in interaction_rows]

    # ── Salesperson Performance (Bar chart) ──
    sp_rows = (await db.execute(
        select(
            Salesperson.id,
            Salesperson.name,
            func.count(Lead.id).label("total_leads"),
            func.sum(case((Lead.status == "ליד חדש", 1), else_=0)).label("new_leads"),
            func.sum(case((Lead.status == "converted", 1), else_=0)).label("converted"),
            func.sum(case((Lead.status.in_(["ליד בתהליך", "חיוג ראשון"]), 1), else_=0)).label("in_progress"),
        )
        .join(Lead, Lead.salesperson_id == Salesperson.id, isouter=True)
        .where(Salesperson.is_active == True)  # noqa: E712
        .where((Lead.created_at >= start) | (Lead.created_at.is_(None)))
        .where((Lead.created_at <= end) | (Lead.created_at.is_(None)))
        .group_by(Salesperson.id, Salesperson.name)
        .order_by(func.count(Lead.id).desc())
    )).all()

    salesperson_performance = []
    for sp in sp_rows:
        # Count interactions per salesperson
        sp_interactions = (await db.execute(
            select(func.count(LeadInteraction.id))
            .join(Lead, Lead.id == LeadInteraction.lead_id)
            .where(Lead.salesperson_id == sp.id)
            .where(LeadInteraction.created_at >= start, LeadInteraction.created_at <= end)
        )).scalar() or 0

        # Count open tasks
        sp_tasks = (await db.execute(
            select(func.count(SalesTask.id))
            .where(SalesTask.salesperson_id == sp.id)
            .where(SalesTask.status != "הושלם")
        )).scalar() or 0

        rate = round((sp.converted / sp.total_leads * 100), 1) if sp.total_leads > 0 else 0
        salesperson_performance.append({
            "id": sp.id,
            "name": sp.name,
            "total_leads": sp.total_leads,
            "new_leads": sp.new_leads,
            "converted": sp.converted,
            "in_progress": sp.in_progress,
            "conversion_rate": rate,
            "interactions": sp_interactions,
            "open_tasks": sp_tasks,
        })

    # ── Lead Response Distribution ──
    response_rows = (await db.execute(
        select(
            func.coalesce(Lead.lead_response, "ללא תגובה").label("response"),
            func.count(Lead.id).label("count"),
        )
        .where(Lead.created_at >= start, Lead.created_at <= end)
        .group_by(Lead.lead_response)
        .order_by(func.count(Lead.id).desc())
    )).all()
    lead_responses = [{"response": r.response, "count": r.count} for r in response_rows]

    return {
        "period": {"from": str(start.date()), "to": str(end.date()), "days": period_length},
        "kpis": kpis,
        "status_distribution": status_distribution,
        "lead_trends": lead_trends,
        "funnel": funnel,
        "source_breakdown": source_breakdown,
        "interaction_types": interaction_types,
        "salesperson_performance": salesperson_performance,
        "lead_responses": lead_responses,
    }
