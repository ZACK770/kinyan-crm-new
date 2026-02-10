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
    )
    db.add(lead)
    await db.flush()
    return lead


# ============================================================
# Update
# ============================================================
async def update_lead(db: AsyncSession, lead_id: int, **kwargs) -> Lead | None:
    """Update lead fields."""
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(lead, key):
            setattr(lead, key, value)

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
# Round-Robin Assignment
# ============================================================
def _phone_hash(phone: str) -> int:
    """Deterministic hash from phone number (same algo as JS version)."""
    clean = "".join(c for c in phone if c.isdigit())
    h = 0
    for ch in clean:
        h = ((h << 5) - h) + ord(ch)
        h &= 0xFFFFFFFF  # 32-bit
    return h


async def assign_salesperson(db: AsyncSession, lead_id: int, phone: str) -> Salesperson | None:
    """Assign salesperson via deterministic round-robin based on phone hash."""
    stmt = select(Salesperson).where(Salesperson.is_active == True).order_by(Salesperson.id)  # noqa: E712
    result = await db.execute(stmt)
    active = result.scalars().all()

    if not active:
        return None

    idx = _phone_hash(phone) % len(active)
    chosen = active[idx]

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
    """
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
        # New lead → create + assign + interaction
        lead = await create_lead(db, **kwargs)
        sp = await assign_salesperson(db, lead.id, phone)
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


async def list_leads(
    db: AsyncSession,
    status: str | None = None,
    salesperson_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Lead]:
    """List leads with optional filters."""
    stmt = select(Lead).order_by(Lead.created_at.desc()).limit(limit).offset(offset)

    if status:
        stmt = stmt.where(Lead.status == status)
    if salesperson_id:
        stmt = stmt.where(Lead.salesperson_id == salesperson_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())
