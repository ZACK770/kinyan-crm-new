"""
Lead management service.
Replaces unified_make_module.js (575 lines JS → ~150 lines Python)
"""
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Lead, LeadInteraction, Salesperson
from utils.phone import normalize_phone, is_valid_phone


# ============================================================
# Search
# ============================================================
async def search_by_phone(db: AsyncSession, phone: str) -> Lead | None:
    """Search lead by phone. Tries exact match, then without leading 0."""
    clean = normalize_phone(phone)
    if not clean:
        return None

    # Exact match
    stmt = select(Lead).where(Lead.phone == clean).limit(1)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if lead:
        return lead

    # Without leading zero (catches +972 stored numbers)
    if clean.startswith("0"):
        short = clean[1:]
        stmt = select(Lead).where(Lead.phone.contains(short)).limit(1)
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()
        if lead:
            return lead

    return None


# ============================================================
# Create
# ============================================================
async def create_lead(db: AsyncSession, **kwargs) -> Lead:
    """Create a new lead."""
    from datetime import datetime, timezone
    
    # Support both 'name' (from webhooks) and 'full_name' (from frontend)
    full_name = kwargs.get("full_name") or kwargs.get("name", "")
    lead = Lead(
        full_name=full_name,
        family_name=kwargs.get("family_name"),
        phone=normalize_phone(kwargs.get("phone", "")),
        phone2=kwargs.get("phone2"),
        email=kwargs.get("email"),
        address=kwargs.get("address"),
        city=kwargs.get("city"),
        id_number=kwargs.get("id_number"),
        notes=kwargs.get("notes"),
        source_type=kwargs.get("source_type"),
        source_name=kwargs.get("source_name"),
        campaign_name=kwargs.get("campaign_name"),
        source_message=kwargs.get("source_message"),
        source_details=kwargs.get("source_details"),
        salesperson_id=kwargs.get("salesperson_id"),
        campaign_id=kwargs.get("campaign_id"),
        course_id=kwargs.get("course_id"),
        requested_course=kwargs.get("form_product") or kwargs.get("requested_course"),
        created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
    )
    db.add(lead)
    await db.flush()
    return lead


# ============================================================
# Update
# ============================================================
async def update_lead(db: AsyncSession, lead_id: int, manual_edit: bool = False, **kwargs) -> Lead | None:
    """Update lead fields. If manual_edit=True, also sets last_edited_at."""
    from datetime import datetime, timezone
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(lead, key):
            setattr(lead, key, value)

    if manual_edit:
        lead.last_edited_at = datetime.now(timezone.utc)

    await db.flush()
    return lead


# ============================================================
# Interactions
# ============================================================
async def add_interaction(db: AsyncSession, lead_id: int, **kwargs) -> LeadInteraction:
    """Add an interaction (call, form submission, etc.) to a lead."""
    interaction = LeadInteraction(
        lead_id=lead_id,
        interaction_type=kwargs.get("interaction_type", "generic"),
        call_status=kwargs.get("call_status"),
        wait_time=kwargs.get("wait_time"),
        call_duration=kwargs.get("call_duration"),
        total_duration=kwargs.get("total_duration"),
        ivr_product=kwargs.get("ivr_product"),
        form_product=kwargs.get("form_product"),
        form_content=kwargs.get("form_content"),
        user_name=kwargs.get("user_name"),
        description=kwargs.get("description"),
    )
    db.add(interaction)
    await db.flush()
    return interaction


# ============================================================
# Smart Lead Assignment with Rules
# ============================================================
async def assign_salesperson(db: AsyncSession, lead_id: int, phone: str) -> Salesperson | None:
    """
    Smart salesperson assignment with workload control, daily limits, and priority weights.
    
    Algorithm:
    1. Get all active salespeople with their assignment rules
    2. Filter out those who reached limits (daily/workload)
    3. Select using weighted random based on priority_weight
    4. Update counters and assign
    5. Fallback to simple round-robin if no rules exist
    """
    from db.models import SalesAssignmentRules
    from datetime import date as date_type
    import random
    
    # Get active salespeople with their rules
    stmt = (
        select(Salesperson, SalesAssignmentRules)
        .outerjoin(SalesAssignmentRules, Salesperson.id == SalesAssignmentRules.salesperson_id)
        .where(Salesperson.is_active == True)  # noqa: E712
        .order_by(Salesperson.id)
    )
    result = await db.execute(stmt)
    salespeople_with_rules = result.all()
    
    if not salespeople_with_rules:
        return None
    
    # Check if any rules exist
    has_rules = any(rules is not None for _, rules in salespeople_with_rules)
    
    if not has_rules:
        # Fallback to simple round-robin
        return await _assign_salesperson_simple(db, lead_id, phone, [sp for sp, _ in salespeople_with_rules])
    
    # Filter available salespeople based on rules
    today = date_type.today()
    available = []
    
    for salesperson, rules in salespeople_with_rules:
        if rules is None:
            # No rules = always available with default weight
            available.append((salesperson, 1))
            continue
        
        if not rules.is_active:
            continue
        
        # Reset daily counter if needed
        if rules.last_reset_date != today:
            rules.daily_leads_assigned = 0
            rules.last_reset_date = today
            await db.flush()
        
        # Check daily limit
        if rules.daily_lead_limit is not None and rules.daily_leads_assigned >= rules.daily_lead_limit:
            continue
        
        # Check workload limit (count open leads)
        if rules.max_open_leads is not None:
            status_filters = rules.status_filters or ["ליד חדש", "ליד בתהליך", "חיוג ראשון"]
            open_leads_stmt = (
                select(func.count(Lead.id))
                .where(Lead.salesperson_id == salesperson.id)
                .where(Lead.status.in_(status_filters))
            )
            open_count_result = await db.execute(open_leads_stmt)
            open_count = open_count_result.scalar()
            
            if open_count >= rules.max_open_leads:
                continue
        
        # Available with priority weight
        available.append((salesperson, rules.priority_weight))
    
    if not available:
        # No one available - fallback to simple assignment (ignore rules)
        return await _assign_salesperson_simple(db, lead_id, phone, [sp for sp, _ in salespeople_with_rules])
    
    # Weighted random selection
    salespeople, weights = zip(*available)
    chosen = random.choices(salespeople, weights=weights, k=1)[0]
    
    # Update lead assignment
    lead_stmt = select(Lead).where(Lead.id == lead_id)
    lead_result = await db.execute(lead_stmt)
    lead = lead_result.scalar_one_or_none()
    if lead:
        lead.salesperson_id = chosen.id
        await db.flush()
    
    # Update daily counter
    rules_stmt = select(SalesAssignmentRules).where(SalesAssignmentRules.salesperson_id == chosen.id)
    rules_result = await db.execute(rules_stmt)
    rules = rules_result.scalar_one_or_none()
    if rules:
        rules.daily_leads_assigned += 1
        await db.flush()
    
    return chosen


async def _assign_salesperson_simple(db: AsyncSession, lead_id: int, phone: str, salespeople: list) -> Salesperson | None:
    """Simple round-robin fallback (original algorithm)."""
    if not salespeople:
        return None
    
    # Deterministic hash from phone number
    clean = "".join(c for c in phone if c.isdigit())
    h = 0
    for ch in clean:
        h = ((h << 5) - h) + ord(ch)
        h &= 0xFFFFFFFF  # 32-bit
    
    idx = h % len(salespeople)
    chosen = salespeople[idx]
    
    lead_stmt = select(Lead).where(Lead.id == lead_id)
    lead_result = await db.execute(lead_stmt)
    lead = lead_result.scalar_one_or_none()
    if lead:
        lead.salesperson_id = chosen.id
        await db.flush()
    
    return chosen


# ============================================================
# Lead Conversion — Convert Lead to Student + Enrollment
# ============================================================
async def convert_lead_to_student(
    db: AsyncSession, 
    lead_id: int, 
    course_id: int | None = None
) -> dict:
    """
    Convert a lead to a student.
    1. Creates Student record from Lead data
    2. Creates Enrollment if course_id provided
    3. Updates Lead with student_id and conversion info
    """
    from db.models import Student, Enrollment
    from datetime import datetime
    
    # Get the lead
    lead = await get_lead_with_history(db, lead_id)
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    if lead.student_id:
        return {"success": False, "error": "Lead already converted", "student_id": lead.student_id}
    
    # Create student from lead data
    student = Student(
        full_name=lead.full_name,
        phone=lead.phone,
        phone2=lead.phone2,
        email=lead.email,
        city=lead.city,
        address=lead.address,
        id_number=lead.id_number,
        notes=lead.notes,
        status="active",
        payment_status="pending",
        lead_id=lead.id,
    )
    db.add(student)
    await db.flush()
    
    enrollment = None
    
    # Create enrollment if course specified
    if course_id:
        enrollment = Enrollment(
            student_id=student.id,
            course_id=course_id,
            status="active",
            current_module=1,
        )
        db.add(enrollment)
        await db.flush()
    
    # Update lead with conversion info
    lead.student_id = student.id
    lead.status = "converted"
    lead.conversion_date = datetime.now()
    
    await db.commit()
    
    return {
        "success": True,
        "student_id": student.id,
        "enrollment_id": enrollment.id if enrollment else None,
        "message": f"ליד הומר לתלמיד #{student.id}" + (f" ונרשם לקורס" if enrollment else ""),
    }


# ============================================================
# Full flow (replaces main() in unified_make_module.js)
# ============================================================
async def process_incoming_lead(db: AsyncSession, **kwargs) -> dict:
    """
    Handle an incoming lead from any source.
    This is the core function that replaces the entire unified_make_module.js.
    
    Flow:
    1. Validate phone
    2. Search for existing lead by phone
       - Found → add interaction
       - Not found → create lead + assign salesperson + add interaction + notify
    """
    from services.lead_notifications import notify_salesperson_new_lead
    
    phone = kwargs.get("phone", "")
    if not is_valid_phone(phone):
        return {"success": False, "error": "Invalid phone number"}

    phone = normalize_phone(phone)
    existing = await search_by_phone(db, phone)

    if existing:
        # Existing lead → add interaction
        await add_interaction(db, existing.id, **kwargs)
        await db.commit()
        return {
            "success": True,
            "action": "updated",
            "lead_id": existing.id,
        }
    else:
        # New lead → create + assign + interaction + notify
        lead = await create_lead(db, **kwargs)
        sp = await assign_salesperson(db, lead.id, phone)
        await add_interaction(db, lead.id, **kwargs)
        await db.commit()
        
        # Post-hook: notify assigned salesperson
        notification_result = None
        if sp:
            try:
                notification_result = await notify_salesperson_new_lead(
                    db,
                    lead_id=lead.id,
                    salesperson_id=sp.id,
                    source=kwargs.get("source_type", "webhook"),
                )
            except Exception as e:
                # Notification failure should never break lead creation
                import logging
                logging.getLogger(__name__).error(f"Notification error for lead {lead.id}: {e}")
        
        return {
            "success": True,
            "action": "created",
            "lead_id": lead.id,
            "salesperson": sp.name if sp else None,
            "notification": notification_result,
        }


# ============================================================
# Queries
# ============================================================
async def get_lead_with_history(db: AsyncSession, lead_id: int) -> Lead | None:
    """Get a lead with all interactions loaded."""
    stmt = (
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.interactions),
            selectinload(Lead.salesperson),
            selectinload(Lead.products),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_leads(
    db: AsyncSession,
    status: str | None = None,
    salesperson_id: int | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Lead]:
    """List leads with optional filters and server-side search."""
    stmt = select(Lead).order_by(Lead.created_at.desc()).limit(limit).offset(offset)

    if status:
        stmt = stmt.where(Lead.status == status)
    if salesperson_id:
        stmt = stmt.where(Lead.salesperson_id == salesperson_id)
    if search:
        q = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Lead.full_name.ilike(q),
                Lead.family_name.ilike(q),
                Lead.phone.ilike(q),
                Lead.phone2.ilike(q),
                Lead.email.ilike(q),
                Lead.city.ilike(q),
            )
        )

    result = await db.execute(stmt)
    return list(result.scalars().all())


# ============================================================
# Discount & Pricing Calculations
# ============================================================
def calculate_discount(
    original_price: float,
    discount_amount: float = 0,
) -> tuple[float, float]:
    """
    חישוב הנחה ומחיר סופי.
    
    Args:
        original_price: מחיר מקורי
        discount_amount: סכום הנחה (תמיד סכום קבוע)
    
    Returns:
        tuple: (סכום_הנחה, מחיר_סופי)
    """
    final_price = max(0, original_price - discount_amount)
    return discount_amount, final_price


async def update_lead_discount(
    db: AsyncSession,
    lead_id: int,
    discount_amount: float,
    installments_override: int | None = None,
) -> dict:
    """
    עדכון הנחה ומחיר סופי לליד.
    
    Args:
        lead_id: מזהה ליד
        discount_amount: סכום הנחה בש"ח
        installments_override: דריסת מספר תשלומים (אופציונלי)
    
    Returns:
        dict עם המחירים המעודכנים
    """
    # Get lead
    lead = await get_lead_with_history(db, lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    
    if not lead.selected_course_id or not lead.selected_price:
        raise ValueError("No course selected for this lead")
    
    # Calculate final price
    original_price = float(lead.selected_price)
    _, final_price = calculate_discount(original_price, discount_amount)
    
    # Update lead pricing
    lead.selected_price = final_price
    
    # Update installments if provided
    if installments_override is not None:
        lead.selected_payments_count = installments_override
    
    # Calculate monthly payment
    payments_count = lead.selected_payments_count or 1
    monthly_payment = final_price / payments_count if payments_count > 0 else final_price
    
    await db.flush()
    
    return {
        "original_price": original_price,
        "discount_amount": discount_amount,
        "final_price": final_price,
        "payments_count": payments_count,
        "monthly_payment": monthly_payment,
    }
