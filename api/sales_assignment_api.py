"""
Sales Assignment Rules API endpoints.
Manage smart lead assignment with daily limits, priority weights, and workload control.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import SalesAssignmentRules, Salesperson, Lead
from services import audit_logs
from .dependencies import require_entity_access, require_permission

router = APIRouter(tags=["sales-assignment"])


# ── Schemas ────────────────────────────────────────
class AssignmentRulesResponse(BaseModel):
    id: int
    salesperson_id: int
    salesperson_name: str
    daily_lead_limit: int | None
    daily_leads_assigned: int
    last_reset_date: str | None
    priority_weight: int
    max_open_leads: int | None
    status_filters: list[str] | None
    is_active: bool
    current_open_leads: int | None = None


class AssignmentRulesUpdate(BaseModel):
    daily_lead_limit: int | None = Field(None, ge=0, description="מגבלת לידים יומית (NULL = ללא הגבלה)")
    priority_weight: int = Field(1, ge=1, le=10, description="משקל העדפה (1-10, גבוה יותר = יותר לידים)")
    max_open_leads: int | None = Field(None, ge=0, description="מקסימום לידים פתוחים (NULL = ללא הגבלה)")
    status_filters: list[str] | None = Field(None, description="סטטוסים לספירת עומס")
    is_active: bool = Field(True, description="האם הכללים פעילים")


class AssignmentRulesCreate(BaseModel):
    salesperson_id: int
    daily_lead_limit: int | None = None
    priority_weight: int = Field(1, ge=1, le=10)
    max_open_leads: int | None = None
    status_filters: list[str] | None = Field(default=["ליד חדש", "במעקב", "מתעניין"])
    is_active: bool = True


class AssignmentStats(BaseModel):
    salesperson_id: int
    salesperson_name: str
    total_leads: int
    open_leads: int
    daily_assigned: int
    daily_limit: int | None
    priority_weight: int
    is_available: bool
    availability_reason: str | None


# ── Endpoints ────────────────────────────────────────
@router.get("/", response_model=list[AssignmentRulesResponse])
async def list_assignment_rules(
    include_stats: bool = Query(False, description="כולל סטטיסטיקות עומס נוכחי"),
    user = Depends(require_entity_access("salespeople", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get all sales assignment rules with optional current workload stats."""
    stmt = (
        select(SalesAssignmentRules, Salesperson)
        .join(Salesperson, SalesAssignmentRules.salesperson_id == Salesperson.id)
        .order_by(Salesperson.name)
    )
    result = await db.execute(stmt)
    rules_with_sp = result.all()
    
    response = []
    for rules, sp in rules_with_sp:
        data = {
            "id": rules.id,
            "salesperson_id": rules.salesperson_id,
            "salesperson_name": sp.name,
            "daily_lead_limit": rules.daily_lead_limit,
            "daily_leads_assigned": rules.daily_leads_assigned,
            "last_reset_date": str(rules.last_reset_date) if rules.last_reset_date else None,
            "priority_weight": rules.priority_weight,
            "max_open_leads": rules.max_open_leads,
            "status_filters": rules.status_filters,
            "is_active": rules.is_active,
        }
        
        if include_stats:
            # Count current open leads
            status_filters = rules.status_filters or ["ליד חדש", "במעקב", "מתעניין"]
            open_stmt = (
                select(func.count(Lead.id))
                .where(Lead.salesperson_id == sp.id)
                .where(Lead.status.in_(status_filters))
            )
            open_result = await db.execute(open_stmt)
            data["current_open_leads"] = open_result.scalar()
        
        response.append(AssignmentRulesResponse(**data))
    
    return response


@router.get("/stats", response_model=list[AssignmentStats])
async def get_assignment_stats(
    user = Depends(require_entity_access("salespeople", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive assignment statistics for all salespeople."""
    today = date.today()
    
    stmt = (
        select(Salesperson, SalesAssignmentRules)
        .outerjoin(SalesAssignmentRules, Salesperson.id == SalesAssignmentRules.salesperson_id)
        .where(Salesperson.is_active == True)  # noqa: E712
        .order_by(Salesperson.name)
    )
    result = await db.execute(stmt)
    salespeople_with_rules = result.all()
    
    stats = []
    for sp, rules in salespeople_with_rules:
        # Count total leads
        total_stmt = select(func.count(Lead.id)).where(Lead.salesperson_id == sp.id)
        total_result = await db.execute(total_stmt)
        total_leads = total_result.scalar()
        
        # Count open leads
        status_filters = rules.status_filters if rules else ["ליד חדש", "במעקב", "מתעניין"]
        open_stmt = (
            select(func.count(Lead.id))
            .where(Lead.salesperson_id == sp.id)
            .where(Lead.status.in_(status_filters))
        )
        open_result = await db.execute(open_stmt)
        open_leads = open_result.scalar()
        
        # Determine availability
        is_available = True
        availability_reason = None
        
        if rules:
            # Check daily limit
            if rules.daily_lead_limit is not None:
                if rules.last_reset_date != today:
                    daily_assigned = 0
                else:
                    daily_assigned = rules.daily_leads_assigned
                
                if daily_assigned >= rules.daily_lead_limit:
                    is_available = False
                    availability_reason = f"הגיע למגבלה יומית ({rules.daily_lead_limit})"
            else:
                daily_assigned = rules.daily_leads_assigned if rules.last_reset_date == today else 0
            
            # Check workload limit
            if is_available and rules.max_open_leads is not None and open_leads >= rules.max_open_leads:
                is_available = False
                availability_reason = f"הגיע למקסימום לידים פתוחים ({rules.max_open_leads})"
            
            if not rules.is_active:
                is_available = False
                availability_reason = "כללים לא פעילים"
            
            priority_weight = rules.priority_weight
            daily_limit = rules.daily_lead_limit
        else:
            daily_assigned = 0
            priority_weight = 1
            daily_limit = None
        
        stats.append(AssignmentStats(
            salesperson_id=sp.id,
            salesperson_name=sp.name,
            total_leads=total_leads,
            open_leads=open_leads,
            daily_assigned=daily_assigned,
            daily_limit=daily_limit,
            priority_weight=priority_weight,
            is_available=is_available,
            availability_reason=availability_reason,
        ))
    
    return stats


@router.get("/salespeople-without-rules", response_model=list[dict])
async def get_salespeople_without_rules(
    user = Depends(require_permission("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get list of active salespeople who don't have assignment rules yet."""
    stmt = (
        select(Salesperson)
        .outerjoin(SalesAssignmentRules, Salesperson.id == SalesAssignmentRules.salesperson_id)
        .where(Salesperson.is_active == True)  # noqa: E712
        .where(SalesAssignmentRules.id.is_(None))
        .order_by(Salesperson.name)
    )
    result = await db.execute(stmt)
    salespeople = result.scalars().all()
    
    return [
        {
            "id": sp.id,
            "name": sp.name,
            "email": sp.email,
            "phone": sp.phone,
        }
        for sp in salespeople
    ]


@router.get("/{salesperson_id}", response_model=AssignmentRulesResponse)
async def get_assignment_rules(
    salesperson_id: int,
    user = Depends(require_entity_access("salespeople", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get assignment rules for a specific salesperson."""
    stmt = (
        select(SalesAssignmentRules, Salesperson)
        .join(Salesperson, SalesAssignmentRules.salesperson_id == Salesperson.id)
        .where(SalesAssignmentRules.salesperson_id == salesperson_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(404, "Assignment rules not found")
    
    rules, sp = row
    
    # Count current open leads
    status_filters = rules.status_filters or ["ליד חדש", "במעקב", "מתעניין"]
    open_stmt = (
        select(func.count(Lead.id))
        .where(Lead.salesperson_id == sp.id)
        .where(Lead.status.in_(status_filters))
    )
    open_result = await db.execute(open_stmt)
    current_open_leads = open_result.scalar()
    
    return AssignmentRulesResponse(
        id=rules.id,
        salesperson_id=rules.salesperson_id,
        salesperson_name=sp.name,
        daily_lead_limit=rules.daily_lead_limit,
        daily_leads_assigned=rules.daily_leads_assigned,
        last_reset_date=str(rules.last_reset_date) if rules.last_reset_date else None,
        priority_weight=rules.priority_weight,
        max_open_leads=rules.max_open_leads,
        status_filters=rules.status_filters,
        is_active=rules.is_active,
        current_open_leads=current_open_leads,
    )


@router.post("/", response_model=AssignmentRulesResponse)
async def create_assignment_rules(
    data: AssignmentRulesCreate,
    request: Request,
    user = Depends(require_entity_access("salespeople", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Create assignment rules for a salesperson."""
    # Check if salesperson exists
    sp_stmt = select(Salesperson).where(Salesperson.id == data.salesperson_id)
    sp_result = await db.execute(sp_stmt)
    sp = sp_result.scalar_one_or_none()
    if not sp:
        raise HTTPException(404, "Salesperson not found")
    
    # Check if rules already exist
    existing_stmt = select(SalesAssignmentRules).where(SalesAssignmentRules.salesperson_id == data.salesperson_id)
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(400, "Assignment rules already exist for this salesperson")
    
    # Create rules
    rules = SalesAssignmentRules(
        salesperson_id=data.salesperson_id,
        daily_lead_limit=data.daily_lead_limit,
        priority_weight=data.priority_weight,
        max_open_leads=data.max_open_leads,
        status_filters=data.status_filters,
        is_active=data.is_active,
        last_reset_date=date.today(),
    )
    db.add(rules)
    await db.flush()
    
    await audit_logs.log_create(
        db=db,
        user=user,
        entity_type="sales_assignment_rules",
        entity_id=rules.id,
        description=f"נוצרו כללי שיוך לאיש מכירות: {sp.name}",
        request=request,
    )
    
    await db.commit()
    
    return AssignmentRulesResponse(
        id=rules.id,
        salesperson_id=rules.salesperson_id,
        salesperson_name=sp.name,
        daily_lead_limit=rules.daily_lead_limit,
        daily_leads_assigned=rules.daily_leads_assigned,
        last_reset_date=str(rules.last_reset_date) if rules.last_reset_date else None,
        priority_weight=rules.priority_weight,
        max_open_leads=rules.max_open_leads,
        status_filters=rules.status_filters,
        is_active=rules.is_active,
    )


@router.patch("/{salesperson_id}", response_model=AssignmentRulesResponse)
async def update_assignment_rules(
    salesperson_id: int,
    data: AssignmentRulesUpdate,
    request: Request,
    user = Depends(require_entity_access("salespeople", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Update assignment rules for a salesperson."""
    stmt = (
        select(SalesAssignmentRules, Salesperson)
        .join(Salesperson, SalesAssignmentRules.salesperson_id == Salesperson.id)
        .where(SalesAssignmentRules.salesperson_id == salesperson_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(404, "Assignment rules not found")
    
    rules, sp = row
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rules, key, value)
    
    await db.flush()
    
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="sales_assignment_rules",
        entity_id=rules.id,
        description=f"עודכנו כללי שיוך לאיש מכירות: {sp.name}",
        changes=update_data,
        request=request,
    )
    
    await db.commit()
    
    return AssignmentRulesResponse(
        id=rules.id,
        salesperson_id=rules.salesperson_id,
        salesperson_name=sp.name,
        daily_lead_limit=rules.daily_lead_limit,
        daily_leads_assigned=rules.daily_leads_assigned,
        last_reset_date=str(rules.last_reset_date) if rules.last_reset_date else None,
        priority_weight=rules.priority_weight,
        max_open_leads=rules.max_open_leads,
        status_filters=rules.status_filters,
        is_active=rules.is_active,
    )


@router.post("/reset-daily-counts")
async def reset_daily_counts(
    request: Request,
    user = Depends(require_entity_access("salespeople", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Manually reset all daily lead counters (useful for testing or manual intervention)."""
    stmt = select(SalesAssignmentRules)
    result = await db.execute(stmt)
    all_rules = result.scalars().all()
    
    today = date.today()
    count = 0
    for rules in all_rules:
        rules.daily_leads_assigned = 0
        rules.last_reset_date = today
        count += 1
    
    await db.flush()
    
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="sales_assignment_rules",
        entity_id=0,
        description=f"אופסו ספירות יומיות עבור {count} אנשי מכירות",
        changes={"action": "reset_daily_counts", "count": count},
        request=request,
    )
    
    await db.commit()
    
    return {"success": True, "count": count, "message": f"אופסו ספירות יומיות עבור {count} אנשי מכירות"}


@router.delete("/{salesperson_id}")
async def delete_assignment_rules(
    salesperson_id: int,
    request: Request,
    user = Depends(require_entity_access("salespeople", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Delete assignment rules for a salesperson (reverts to default round-robin)."""
    stmt = select(SalesAssignmentRules).where(SalesAssignmentRules.salesperson_id == salesperson_id)
    result = await db.execute(stmt)
    rules = result.scalar_one_or_none()
    
    if not rules:
        raise HTTPException(404, "Assignment rules not found")
    
    await db.delete(rules)
    
    await audit_logs.log_delete(
        db=db,
        user=user,
        entity_type="sales_assignment_rules",
        entity_id=rules.id,
        description=f"נמחקו כללי שיוך לאיש מכירות #{salesperson_id}",
        request=request,
    )
    
    await db.commit()
    
    return {"success": True, "message": "כללי השיוך נמחקו בהצלחה"}
