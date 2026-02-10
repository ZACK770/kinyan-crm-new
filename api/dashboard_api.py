"""
Dashboard API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import Lead, Student, Enrollment, Payment, Salesperson
from services import sales as sales_svc
from .dependencies import require_permission

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


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
