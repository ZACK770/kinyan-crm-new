"""
Lead management service.
Replaces unified_make_module.js (575 lines JS → ~150 lines Python)
"""
from sqlalchemy import select, or_, func
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
    # Support both 'name' (from webhooks) and 'full_name' (from frontend)
    full_name = kwargs.get("full_name") or kwargs.get("name", "")
    
    phone = normalize_phone(kwargs.get("phone", ""))
    
    lead = Lead(
        full_name=full_name,
        family_name=kwargs.get("family_name"),
        phone=phone,
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
        requested_course=kwargs.get("requested_course"),
    )
    db.add(lead)
    await db.flush()
    return lead


# ============================================================
# Update
# ============================================================
async def update_lead(db: AsyncSession, lead_id: int, **kwargs) -> Lead | None:
    """Update lead fields."""
    from datetime import datetime

    print(f"🔧 [SERVICE] Starting update_lead for lead_id={lead_id}")
    print(f"📥 [SERVICE] Update kwargs: {kwargs}")
    print(f"📊 [SERVICE] Number of fields to update: {len(kwargs)}")
    
    # Query the lead
    print(f"🔍 [SERVICE] Querying database for lead {lead_id}")
    stmt = select(Lead).where(Lead.id == lead_id)
    
    try:
        result = await db.execute(stmt)
        print(f"✅ [SERVICE] Database query executed successfully")
    except Exception as e:
        print(f"❌ [SERVICE] Database query failed: {e}")
        raise
    
    lead = result.scalar_one_or_none()
    if not lead:
        print(f"❌ [SERVICE] Lead {lead_id} not found in database")
        return None

    print(f"✅ [SERVICE] Lead found: {lead.full_name} (current status: {lead.status})")
    print(f"📊 [SERVICE] Lead current values before update:")
    for key in kwargs.keys():
        if hasattr(lead, key):
            current_value = getattr(lead, key)
            print(f"  - {key}: {current_value} (type: {type(current_value)})")

    # Track if status or salesperson_id changed (manual edits by salesperson)
    # Actually, any update via this service from the UI should probably be considered a manual edit
    is_manual_edit = True 
    print(f"🏷️ [SERVICE] Marking as manual edit for last_edited_at update")

    # Apply updates
    print(f"🔄 [SERVICE] Applying field updates...")
    updated_fields = []
    for key, value in kwargs.items():
        if hasattr(lead, key):
            old_value = getattr(lead, key)
            if old_value != value:
                print(f"🔧 [SERVICE] Updating {key}: {old_value} → {value} (type: {type(value)})")
                setattr(lead, key, value)
                updated_fields.append(key)
            else:
                print(f"ℹ️ [SERVICE] Field {key} value is unchanged, skipping")
        else:
            print(f"⚠️ [SERVICE] Field {key} does not exist on Lead model, skipping")

    if not updated_fields:
        print(f"ℹ️ [SERVICE] No fields were actually changed for lead {lead_id}")
        return lead

    print(f"✅ [SERVICE] Actually updated {len(updated_fields)} fields: {updated_fields}")

    # Update last_edited_at for manual edits
    if is_manual_edit:
        lead.last_edited_at = datetime.now()
        print(f"📅 [SERVICE] Updated last_edited_at to now()")

    # Flush changes to database
    print(f"💾 [SERVICE] Flushing changes to database...")
    try:
        await db.flush()
        print(f"✅ [SERVICE] Database flush successful")
    except Exception as e:
        print(f"❌ [SERVICE] Database flush failed: {e}")
        raise

    # Verify updates
    print(f"🔍 [SERVICE] Verifying updates after flush:")
    for key in updated_fields:
        new_value = getattr(lead, key)
        print(f"  - {key}: {new_value}")
    
    print(f"✅ [SERVICE] Lead update completed successfully for lead {lead_id}")
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
    
    # Touch the lead to trigger updated_at update
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if lead:
        # Force update the updated_at field to current time
        from sqlalchemy import func
        lead.updated_at = func.now()
    
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
            status_filters = rules.status_filters or ["ליד חדש", "במעקב", "מתעניין"]
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
    
    # Check if all conversion checklist items are completed
    if not lead.approved_terms:
        return {"success": False, "error": "הליד לא אישר את התקנון"}
    
    if not lead.shipping_details_complete:
        return {"success": False, "error": "הליד לא קיבל את המשלוח"}
    
    if not lead.student_chat_added:
        return {"success": False, "error": "הליד לא הוכנס לרשימת צינתוקים"}
    
    if not lead.personal_course_update:
        return {"success": False, "error": "הליד לא עודכן אישית על מיקום ושעת הקורס הקרוב"}
    
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
    lead.conversion_checklist_complete = True
    lead.conversion_completed_at = datetime.now()
    
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
    """
    phone = kwargs.get("phone", "")
    
    # Normalize phone (basic cleanup, no validation)
    phone = normalize_phone(phone)
    
    # If phone is empty, use a placeholder to satisfy DB constraint
    if not phone:
        phone = f"no_phone_{kwargs.get('name', 'unknown')}"
    
    existing = await search_by_phone(db, phone)

    if existing:
        # Existing lead → add interaction
        await add_interaction(db, existing.id, **kwargs)
        
        # Update salesperson if explicitly provided (e.g., from Yemot Folder routing)
        if kwargs.get("salesperson_id"):
            old_sp_id = existing.salesperson_id
            new_sp_id = kwargs["salesperson_id"]
            
            if old_sp_id != new_sp_id:
                # Get salesperson names for the history log
                old_sp_name = ""
                new_sp_name = ""
                
                if old_sp_id:
                    old_sp_stmt = select(Salesperson).where(Salesperson.id == old_sp_id)
                    old_sp_result = await db.execute(old_sp_stmt)
                    old_sp = old_sp_result.scalar_one_or_none()
                    old_sp_name = old_sp.name if old_sp else f"ID {old_sp_id}"
                
                if new_sp_id:
                    new_sp_stmt = select(Salesperson).where(Salesperson.id == new_sp_id)
                    new_sp_result = await db.execute(new_sp_stmt)
                    new_sp = new_sp_result.scalar_one_or_none()
                    new_sp_name = new_sp.name if new_sp else f"ID {new_sp_id}"
                
                # Update the salesperson
                existing.salesperson_id = new_sp_id
                await db.flush()
                
                # Add interaction to history
                await add_interaction(
                    db,
                    existing.id,
                    interaction_type="salesperson_change",
                    description=f"איש מכירות עודכן מ '{old_sp_name}' ל '{new_sp_name}' (וובהוק)"
                )
        
        await db.commit()
        return {
            "success": True,
            "action": "updated",
            "lead_id": existing.id,
        }
    else:
        # New lead → create + assign + interaction
        lead = await create_lead(db, **kwargs)
        
        # Only auto-assign if salesperson_id was not explicitly provided
        if not kwargs.get("salesperson_id"):
            sp = await assign_salesperson(db, lead.id, phone)
        else:
            # Load the assigned salesperson for the response
            sp_stmt = select(Salesperson).where(Salesperson.id == lead.salesperson_id)
            sp_result = await db.execute(sp_stmt)
            sp = sp_result.scalar_one_or_none()
        
        await add_interaction(db, lead.id, **kwargs)
        await db.commit()
        return {
            "success": True,
            "action": "created",
            "lead_id": lead.id,
            "salesperson": sp.name if sp else None,
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


async def get_lead_with_full_history(db: AsyncSession, lead_id: int) -> dict:
    """Get a lead with interactions AND history entries combined."""
    from db.models import HistoryEntry
    
    print(f"[get_lead_with_full_history] Starting for lead_id: {lead_id}")
    
    # Get lead with interactions
    lead = await get_lead_with_history(db, lead_id)
    if not lead:
        print(f"[get_lead_with_full_history] Lead not found: {lead_id}")
        return None
    
    print(f"[get_lead_with_full_history] Lead found: {lead.id}, interactions count: {len(lead.interactions or [])}")
    
    # Get history entries for this lead
    history_stmt = select(HistoryEntry).where(HistoryEntry.lead_id == lead_id).order_by(HistoryEntry.created_at.desc())
    history_result = await db.execute(history_stmt)
    history_entries = list(history_result.scalars().all())
    
    print(f"[get_lead_with_full_history] History entries count: {len(history_entries)}")
    for entry in history_entries:
        print(f"[get_lead_with_full_history]   - Entry ID: {entry.id}, action_type: {entry.action_type}, description: {entry.description}")
    
    # Combine interactions and history entries into a single timeline
    timeline = []
    
    # Add interactions
    for interaction in lead.interactions or []:
        timeline.append({
            "id": f"interaction_{interaction.id}",
            "type": "interaction",
            "interaction_type": interaction.interaction_type,
            "description": interaction.description,
            "call_status": interaction.call_status,
            "user_name": interaction.user_name,
            "created_at": interaction.created_at,
        })
    
    print(f"[get_lead_with_full_history] Added {len(lead.interactions or [])} interactions to timeline")
    
    # Add history entries (mapped to interaction format)
    for entry in history_entries:
        timeline.append({
            "id": f"history_{entry.id}",
            "type": "history",
            "interaction_type": entry.action_type,
            "description": entry.description,
            "call_status": None,
            "user_name": None,
            "created_at": entry.created_at,
            "extra_data": entry.extra_data,
        })
    
    print(f"[get_lead_with_full_history] Added {len(history_entries)} history entries to timeline")
    
    # Sort by created_at
    timeline.sort(key=lambda x: x["created_at"], reverse=True)
    
    print(f"[get_lead_with_full_history] Total timeline items after sorting: {len(timeline)}")
    for item in timeline:
        print(f"[get_lead_with_full_history]   - Timeline item: type={item['type']}, interaction_type={item.get('interaction_type')}, created_at={item['created_at']}")
    
    return {
        "lead": lead,
        "timeline": timeline,
    }


async def list_leads(
    db: AsyncSession,
    status: str | None = None,
    salesperson_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Lead]:
    """List leads with optional filters. Loads only the last interaction for performance."""
    from db.models import LeadInteraction
    from sqlalchemy.orm import joinedload

    # Load leads with their interactions
    stmt = (
        select(Lead)
        .options(
            joinedload(Lead.interactions)
        )
        .order_by(Lead.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status:
        stmt = stmt.where(Lead.status == status)
    if salesperson_id:
        stmt = stmt.where(Lead.salesperson_id == salesperson_id)

    result = await db.execute(stmt)
    leads = list(result.unique().scalars().all())

    # Filter to keep only the last interaction for each lead
    for lead in leads:
        if lead.interactions and len(lead.interactions) > 0:
            # Sort interactions by created_at desc and keep only the first
            lead.interactions.sort(key=lambda x: x.created_at, reverse=True)
            lead.interactions = [lead.interactions[0]]

    return leads


async def bulk_delete_leads(db: AsyncSession, lead_ids: list[int]) -> dict:
    """
    Delete multiple leads by their IDs.
    
    Args:
        db: Database session
        lead_ids: List of lead IDs to delete
    
    Returns:
        dict with success status and count of deleted leads
    """
    if not lead_ids:
        return {"success": True, "deleted_count": 0, "message": "No leads to delete"}
    
    # First, get the leads to verify they exist
    stmt = select(Lead).where(Lead.id.in_(lead_ids))
    result = await db.execute(stmt)
    existing_leads = result.scalars().all()
    
    if not existing_leads:
        return {"success": False, "error": "No leads found with the provided IDs"}
    
    # Delete related interactions first (foreign key constraint)
    from db.models import LeadInteraction
    interactions_stmt = select(LeadInteraction).where(LeadInteraction.lead_id.in_(lead_ids))
    interactions_result = await db.execute(interactions_stmt)
    interactions = interactions_result.scalars().all()
    
    for interaction in interactions:
        await db.delete(interaction)
    
    # Delete the leads
    deleted_count = 0
    for lead in existing_leads:
        await db.delete(lead)
        deleted_count += 1
    
    await db.flush()
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Successfully deleted {deleted_count} leads"
    }


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


async def bulk_update_leads(db: AsyncSession, lead_ids: list[int], field: str, value: any) -> int:
    """
    Update a specific field for multiple leads.
    """
    if not lead_ids:
        return 0
    
    # Define allowed fields for bulk update
    allowed_fields = {
        "status",
        "salesperson_id",
        "course_id",
        "city",
        "source_type",
        "source_name",
        "campaign_name",
    }
    
    if field not in allowed_fields:
        raise ValueError(f"Field '{field}' is not allowed for bulk update")
    
    # Get leads
    stmt = select(Lead).where(Lead.id.in_(lead_ids))
    result = await db.execute(stmt)
    leads = result.scalars().all()
    
    updated_count = 0
    for lead in leads:
        if hasattr(lead, field):
            setattr(lead, field, value)
            updated_count += 1
    
    if updated_count > 0:
        await db.flush()
        
    return updated_count
