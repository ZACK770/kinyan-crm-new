"""
Leads API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import leads as lead_svc
from services import google_drive_esign
from .dependencies import require_entity_access, get_current_user
from .schemas import LeadCreate, LeadUpdate, SalespersonResponse

router = APIRouter(tags=["leads"])


# ── Local Schemas (not in shared schemas.py) ──────────
class InteractionCreate(BaseModel):
    interaction_type: str = "generic"
    description: str | None = None
    user_name: str | None = None
    next_call_date: datetime | None = None


# ── Endpoints ────────────────────────────────────────
@router.get("/")
async def list_leads(
    status: str | None = Query(None),
    salesperson_id: int | None = Query(None),
    limit: int = Query(50, le=1000),
    offset: int = Query(0),
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await lead_svc.list_leads(db, status=status, salesperson_id=salesperson_id, limit=limit, offset=offset)
    return [
        {
            "id": l.id,
            "full_name": l.full_name,
            "family_name": l.family_name,
            "phone": l.phone,
            "phone2": l.phone2,
            "email": l.email,
            "city": l.city,
            "status": l.status,
            "source_type": l.source_type,
            "source_name": l.source_name,
            "campaign_name": l.campaign_name,
            "requested_course": l.requested_course,
            "arrival_date": str(l.arrival_date) if l.arrival_date else None,
            "salesperson_id": l.salesperson_id,
            "created_at": str(l.created_at),
            "updated_at": str(l.updated_at) if l.updated_at else None,
            "last_edited_at": str(l.last_edited_at) if l.last_edited_at else None,
            "conversion_date": str(l.conversion_date) if l.conversion_date else None,
        }
        for l in items
    ]


@router.get("/search")
async def search_lead(
    phone: str = Query(...),
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db)
):
    lead = await lead_svc.search_by_phone(db, phone)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {"id": lead.id, "full_name": lead.full_name, "phone": lead.phone, "status": lead.status}


@router.get("/salespersons")
async def get_salespersons(
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get list of active salespeople for lead assignment."""
    from services import sales as sales_svc
    salespeople = await sales_svc.get_active_salespeople(db)
    return [
        {"id": sp.id, "name": sp.name, "email": sp.email, "phone": sp.phone}
        for sp in salespeople
    ]


@router.get("/{lead_id}")
async def get_lead(
    lead_id: int,
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db)
):
    lead = await lead_svc.get_lead_with_history(db, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {
        "id": lead.id,
        "full_name": lead.full_name,
        "family_name": lead.family_name,
        "phone": lead.phone,
        "phone2": lead.phone2,
        "email": lead.email,
        "address": lead.address,
        "city": lead.city,
        "id_number": lead.id_number,
        "notes": lead.notes,
        "source_type": lead.source_type,
        "source_name": lead.source_name,
        "campaign_name": lead.campaign_name,
        "source_message": lead.source_message,
        "source_details": lead.source_details,
        "status": lead.status,
        "salesperson_id": lead.salesperson_id,
        "campaign_id": lead.campaign_id,
        "course_id": lead.course_id,
        "student_id": lead.student_id,
        "conversion_date": str(lead.conversion_date) if lead.conversion_date else None,
        "first_payment": lead.first_payment,
        "first_lesson": lead.first_lesson,
        "approved_terms": lead.approved_terms,
        "created_at": str(lead.created_at),
        "updated_at": str(lead.updated_at) if lead.updated_at else None,
        "created_by": lead.created_by,
        "interactions": [
            {
                "id": i.id,
                "interaction_type": i.interaction_type,
                "description": i.description,
                "call_status": i.call_status,
                "user_name": i.user_name,
                "created_at": str(i.created_at),
            }
            for i in (lead.interactions or [])
        ],
    }


@router.post("/")
async def create_lead(
    data: LeadCreate,
    request: Request,
    user = Depends(require_entity_access("leads", "create")),
    db: AsyncSession = Depends(get_db)
):
    result = await lead_svc.process_incoming_lead(db, **data.model_dump())
    
    # Log lead creation
    if result and "lead_id" in result:
        await audit_logs.log_create(
            db=db,
            user=user,
            entity_type="leads",
            entity_id=result["lead_id"],
            description=f"נוצר ליד חדש: {data.full_name} - {data.phone}",
            request=request,
        )
    
    return result


@router.patch("/{lead_id}")
async def update_lead(
    lead_id: int,
    data: LeadUpdate,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    changes = data.model_dump(exclude_unset=True)
    print(f"🔧 [API] update_lead call for lead_id={lead_id}")
    print(f"📥 [API] Changes: {changes}")
    
    try:
        print(f"� [API] Executing update_lead with user={user.email}")
        lead = await lead_svc.update_lead(db, lead_id, **changes)
        
        if not lead:
            print(f"❌ [API] Lead {lead_id} not found")
            raise HTTPException(404, "Lead not found")
        
        print(f"💾 [API] Committing changes to lead {lead_id}")
        await db.commit()
        print(f"✅ [API] Transaction committed")

        # Refresh from DB to get server-computed values
        await db.refresh(lead)
        print(f"🔄 [API] Lead refreshed. Current state in DB: status='{lead.status}', salesperson_id={lead.salesperson_id}")

        # Log lead update
        try:
            print(f"📝 [API] Logging audit update for lead {lead_id}")
            await audit_logs.log_update(
                db=db,
                user=user,
                entity_type="leads",
                entity_id=lead_id,
                description=f"עודכן ליד: {lead.full_name}",
                changes=changes,
                request=request,
            )
        except Exception as e:
            print(f"⚠️ [API] Audit log error (non-fatal): {e}")

        # Return full lead object
        resp_data = {
            "id": lead.id,
            "full_name": lead.full_name,
            "family_name": lead.family_name,
            "phone": lead.phone,
            "phone2": lead.phone2,
            "email": lead.email,
            "city": lead.city,
            "address": lead.address,
            "id_number": lead.id_number,
            "notes": lead.notes,
            "source_type": lead.source_type,
            "source_name": lead.source_name,
            "campaign_name": lead.campaign_name,
            "source_message": lead.source_message,
            "source_details": lead.source_details,
            "status": lead.status,
            "salesperson_id": lead.salesperson_id,
            "campaign_id": lead.campaign_id,
            "course_id": lead.course_id,
            "student_id": lead.student_id,
            "conversion_date": str(lead.conversion_date) if lead.conversion_date else None,
            "first_payment": lead.first_payment,
            "first_lesson": lead.first_lesson,
            "approved_terms": lead.approved_terms,
            "created_at": str(lead.created_at),
            "updated_at": str(lead.updated_at) if lead.updated_at else None,
            "created_by": lead.created_by,
            "last_edited_at": str(lead.last_edited_at) if lead.last_edited_at else None,
        }
        print(f"📤 [API] Returning updated lead data: status='{resp_data['status']}', salesperson_id={resp_data['salesperson_id']}")
        return resp_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [API] CRITICAL ERROR in update_lead: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(500, f"Internal server error: {str(e)}")


# ── Debug Endpoint ────────────────────────────────────────
@router.get("/{lead_id}/debug")
async def debug_lead(
    lead_id: int,
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Remote debug endpoint — returns raw DB values for every field of a lead.
    Useful for diagnosing workspace save issues without server log access.
    GET /api/leads/{id}/debug
    """
    from db.models import Salesperson, Course

    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")

    # Resolve salesperson name
    salesperson_name = None
    salesperson_found = False
    if lead.salesperson_id:
        sp_stmt = select(Salesperson).where(Salesperson.id == lead.salesperson_id)
        sp_result = await db.execute(sp_stmt)
        sp = sp_result.scalar_one_or_none()
        salesperson_name = sp.name if sp else None
        salesperson_found = sp is not None

    # Resolve course name
    course_name = None
    course_found = False
    if lead.course_id:
        c_stmt = select(Course).where(Course.id == lead.course_id)
        c_result = await db.execute(c_stmt)
        c = c_result.scalar_one_or_none()
        course_name = c.name if c else None
        course_found = c is not None

    return {
        "lead_id": lead_id,
        "debug_summary": {
            "status": lead.status,
            "salesperson_id": lead.salesperson_id,
            "salesperson_name": salesperson_name,
            "salesperson_id_valid": salesperson_found if lead.salesperson_id else None,
            "course_id": lead.course_id,
            "course_name": course_name,
            "course_id_valid": course_found if lead.course_id else None,
        },
        "all_fields": {
            "id": lead.id,
            "full_name": lead.full_name,
            "family_name": lead.family_name,
            "phone": lead.phone,
            "phone2": lead.phone2,
            "email": lead.email,
            "address": lead.address,
            "city": lead.city,
            "id_number": lead.id_number,
            "notes": lead.notes,
            "status": lead.status,
            "source_type": lead.source_type,
            "source_name": lead.source_name,
            "campaign_name": lead.campaign_name,
            "source_message": lead.source_message,
            "source_details": lead.source_details,
            "salesperson_id": lead.salesperson_id,
            "campaign_id": lead.campaign_id,
            "course_id": lead.course_id,
            "requested_course": lead.requested_course,
            "student_id": lead.student_id,
            "first_payment": lead.first_payment,
            "first_lesson": lead.first_lesson,
            "approved_terms": lead.approved_terms,
            "created_at": str(lead.created_at),
            "updated_at": str(lead.updated_at) if lead.updated_at else None,
            "last_edited_at": str(lead.last_edited_at) if lead.last_edited_at else None,
            "created_by": lead.created_by,
        },
        "patch_test_instructions": {
            "test_status_update": f"PATCH /api/leads/{lead_id} body: {{\"status\": \"ליד בתהליך\"}}",
            "test_salesperson_update": f"PATCH /api/leads/{lead_id} body: {{\"salesperson_id\": 1}}",
            "test_id_number_update": f"PATCH /api/leads/{lead_id} body: {{\"id_number\": \"000000000\"}}",
            "swagger_ui": "/docs#/leads/update_lead_api_leads__lead_id__patch",
        },
    }


# ── Convert Lead to Student ────────────────────────────────
class ConvertLeadRequest(BaseModel):
    course_id: int | None = None


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: int,
    data: ConvertLeadRequest,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """Convert a lead to a student, optionally enrolling in a course."""
    result = await lead_svc.convert_lead_to_student(db, lead_id, course_id=data.course_id)
    
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Conversion failed"))
    
    # Log conversion
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="leads",
        entity_id=lead_id,
        description=f"ליד הומר לתלמיד #{result.get('student_id')}",
        changes={"action": "converted", "student_id": result.get("student_id"), "course_id": data.course_id},
        request=request,
    )
    
    return result


@router.post("/{lead_id}/interactions")
async def add_interaction(
    lead_id: int,
    data: InteractionCreate,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    interaction = await lead_svc.add_interaction(db, lead_id, **data.model_dump())
    await db.commit()
    return {"id": interaction.id}


# ── Lead Payment Endpoints ────────────────────────────────
class CreatePaymentLinkRequest(BaseModel):
    amount: float | None = None
    currency: str = "ILS"
    installments: int | None = None
    payment_method: str = "credit_card"
    course_id: int | None = None
    redirect_url: str | None = None


@router.post("/{lead_id}/create-payment-link")
async def create_lead_payment_link(
    lead_id: int,
    data: CreatePaymentLinkRequest,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a payment link for a lead via Nedarim Plus.
    Used by sales team to charge leads before conversion.
    """
    from services import nedarim_plus
    
    try:
        result = await nedarim_plus.create_lead_payment_link(
            db=db,
            lead_id=lead_id,
            amount=data.amount,
            currency=data.currency,
            payment_method=data.payment_method,
            installments=data.installments,
            course_id=data.course_id,
            redirect_url=data.redirect_url,
        )
        await db.commit()
        
        # Log payment link creation
        await audit_logs.log_create(
            db=db,
            user=user,
            entity_type="payments",
            entity_id=result["payment_id"],
            description=f"נוצר לינק תשלום לליד #{lead_id} - {data.amount} ש\"ח",
            request=request,
        )
        
        return result
    except Exception as e:
        raise HTTPException(400, str(e))


class SelectCourseRequest(BaseModel):
    course_id: int
    track_id: int | None = None
    price: float | None = None
    payments_count: int = 1
    payment_day: int | None = None
    payment_type: str = "הוראת קבע"
    coupon_id: int | None = None


@router.post("/{lead_id}/select-course")
async def select_course_for_lead(
    lead_id: int,
    data: SelectCourseRequest,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """
    Select/change the course for a lead.
    Updates lead with selected course and pricing details.
    """
    from db.models import Lead, Course, CourseTrack
    from sqlalchemy import select
    
    # Get lead
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    
    # Get course for price if not provided
    stmt = select(Course).where(Course.id == data.course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(404, "Course not found")
    
    # Get track if specified
    track = None
    if data.track_id:
        stmt = select(CourseTrack).where(CourseTrack.id == data.track_id)
        result = await db.execute(stmt)
        track = result.scalar_one_or_none()
        if not track:
            raise HTTPException(404, "Track not found")
    
    # Determine price (track price > course price > provided price)
    price = data.price
    if not price and track and track.price:
        price = float(track.price)
    if not price and course.price:
        price = float(course.price)
    if not price:
        price = 0
    
    # Update lead with selection
    lead.selected_course_id = data.course_id
    lead.selected_price = price
    lead.selected_payments_count = data.payments_count
    lead.selected_payment_day = data.payment_day
    if data.track_id:
        lead.interested_track_id = data.track_id
    
    await db.commit()
    
    # Log course selection
    await audit_logs.log_update(
        db=db,
        user=user,
        entity_type="leads",
        entity_id=lead_id,
        description=f"נבחר קורס לליד: {course.name}" + (f" - מסלול {track.name}" if track else ""),
        changes={"course_id": data.course_id, "track_id": data.track_id, "price": price},
        request=request,
    )
    
    return {
        "lead_id": lead_id,
        "course_id": data.course_id,
        "course_name": course.name,
        "track_id": data.track_id,
        "track_name": track.name if track else None,
        "price": price,
        "payments_count": data.payments_count,
    }


@router.get("/{lead_id}/payment-status")
async def get_lead_payment_status(
    lead_id: int,
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db)
):
    """Get payment status for a lead."""
    from db.models import Lead, Payment
    from sqlalchemy import select
    
    # Get lead
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    
    # Get payments for this lead
    stmt = select(Payment).where(Payment.lead_id == lead_id).order_by(Payment.created_at.desc())
    result = await db.execute(stmt)
    payments = result.scalars().all()
    
    return {
        "lead_id": lead_id,
        "first_payment": lead.first_payment,
        "first_payment_id": lead.first_payment_id,
        "nedarim_payment_link": lead.nedarim_payment_link,
        "selected_course_id": lead.selected_course_id,
        "selected_price": float(lead.selected_price) if lead.selected_price else None,
        "selected_payments_count": lead.selected_payments_count,
        "payments": [
            {
                "id": p.id,
                "amount": float(p.amount),
                "status": p.status,
                "payment_date": str(p.payment_date) if p.payment_date else None,
                "nedarim_donation_id": p.nedarim_donation_id,
                "created_at": str(p.created_at),
            }
            for p in payments
        ]
    }


class UpdateDiscountRequest(BaseModel):
    discount_amount: float = Field(ge=0, description="סכום הנחה בש\"ח")
    installments_override: int | None = Field(None, ge=1, description="דריסת מספר תשלומים")


@router.patch("/{lead_id}/update-discount")
async def update_lead_discount(
    lead_id: int,
    data: UpdateDiscountRequest,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """
    עדכון הנחה ומחיר סופי לליד.
    מחשב אוטומטית את המחיר הסופי והתשלום החודשי.
    """
    try:
        result = await lead_svc.update_lead_discount(
            db=db,
            lead_id=lead_id,
            discount_amount=data.discount_amount,
            installments_override=data.installments_override
        )
        await db.commit()
        
        # Log discount update
        await audit_logs.log_update(
            db=db,
            user=user,
            entity_type="leads",
            entity_id=lead_id,
            description=f"עודכנה הנחה: {data.discount_amount} ש\"ח",
            changes={
                "discount_amount": data.discount_amount,
                "final_price": result["final_price"],
                "installments": data.installments_override
            },
            request=request,
        )
        
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


class GetPricingRequest(BaseModel):
    course_id: int
    track_id: int | None = None
    discount_amount: float = 0


@router.post("/{lead_id}/calculate-pricing")
async def calculate_lead_pricing(
    lead_id: int,
    data: GetPricingRequest,
    user = Depends(require_entity_access("leads", "view")),
    db: AsyncSession = Depends(get_db)
):
    """
    חישוב מקדים של מחיר סופי עם הנחה (ללא שמירה).
    שימושי לתצוגה בזמן אמת בממשק.
    """
    from db.models import Course, CourseTrack
    from sqlalchemy import select
    
    # Get course
    stmt = select(Course).where(Course.id == data.course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(404, "Course not found")
    
    # Get track if specified
    track = None
    if data.track_id:
        stmt = select(CourseTrack).where(CourseTrack.id == data.track_id)
        result = await db.execute(stmt)
        track = result.scalar_one_or_none()
    
    # Determine price (track > course)
    original_price = 0
    if track and track.price:
        original_price = float(track.price)
    elif course.price:
        original_price = float(course.price)
    
    _, final_price = lead_svc.calculate_discount(original_price, data.discount_amount)
    
    payments_count = course.payments_count or 1
    monthly_payment = final_price / payments_count if payments_count > 0 else final_price
    
    return {
        "course_id": data.course_id,
        "course_name": course.name,
        "track_id": data.track_id,
        "track_name": track.name if track else None,
        "original_price": original_price,
        "discount_amount": data.discount_amount,
        "final_price": final_price,
        "payments_count": payments_count,
        "monthly_payment": monthly_payment,
    }


class DirectChargeRequest(BaseModel):
    card_number: str = Field(..., description="מספר כרטיס אשראי (13-16 ספרות)")
    expiry: str = Field(..., description="תוקף MMYY (4 ספרות)")
    cvv: str = Field(..., description="CVV (3-4 ספרות)")
    amount: float | None = Field(None, description="סכום (אם None - לוקח מהליד)")
    installments: int | None = Field(None, description="מספר תשלומים (אם None - לוקח מהליד)")
    payment_type: str = Field("RAGIL", description="סוג תשלום: RAGIL (רגיל) או HK (הוראת קבע)")
    comments: str | None = Field(None, description="הערות")


class BulkDeleteRequest(BaseModel):
    ids: list[int] = Field(..., description="רשימת מזהי הלידים למחיקה")


@router.post("/{lead_id}/charge-card-direct")
async def charge_lead_card_direct(
    lead_id: int,
    data: DirectChargeRequest,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """
    Charge lead's credit card directly via Nedarim Plus DebitCard API.
    This performs immediate credit card charging without payment links.
    """
    from services import nedarim_debit_card
    
    try:
        result = await nedarim_debit_card.charge_lead_card(
            db=db,
            lead_id=lead_id,
            card_number=data.card_number,
            expiry=data.expiry,
            cvv=data.cvv,
            amount=data.amount,
            installments=data.installments,
            payment_type=data.payment_type,
            comments=data.comments,
        )
        await db.commit()
        
        # Log direct charge
        await audit_logs.log_create(
            db=db,
            user=user,
            entity_type="payments",
            entity_id=result["payment_id"],
            description=f"בוצעה סליקה ישירה לליד #{lead_id} - {result['amount']} ש\"ח - אישור: {result['confirmation']}",
            request=request,
        )
        
        return result
    except nedarim_debit_card.NedarimDebitCardError as e:
        raise HTTPException(400, f"סליקה נכשלה: {e.message}")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/{lead_id}/send-esignature")
async def send_esignature(
    lead_id: int,
    template_id: str = Query(..., description="Google Drive Template File ID"),
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a Google Drive document for eSignature to the lead.
    """
    result = await google_drive_esign.send_document_for_signature(
        db=db,
        lead_id=lead_id,
        template_file_id=template_id,
        user_name=user.full_name
    )
    if not result.get("success"):
        raise HTTPException(400, result.get("error"))
    return result



class BulkUpdateRequest(BaseModel):
    ids: list[int]
    field: str
    value: str | int | float | bool | None = None


@router.post("/bulk-update")
async def bulk_update_leads(
    data: BulkUpdateRequest,
    request: Request,
    user = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update multiple leads' fields at once.
    """
    try:
        count = await lead_svc.bulk_update_leads(db, data.ids, data.field, data.value)
        await db.commit()
        
        # Log bulk update
        await audit_logs.log_update(
            db=db,
            user=user,
            entity_type="leads",
            entity_id=None,
            description=f"עדכון גורף של {count} לידים: {data.field}={data.value}",
            changes={"ids": data.ids, "field": data.field, "value": data.value},
            request=request,
        )
        
        return {"updated": count}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))


@router.post("/bulk-delete")
async def bulk_delete_leads(
    data: BulkDeleteRequest,
    request: Request,
    user = Depends(require_entity_access("leads", "delete")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete multiple leads by their IDs.
    Requires delete permission on leads entity.
    """
    try:
        result = await lead_svc.bulk_delete_leads(db, data.ids)
        
        if not result["success"]:
            raise HTTPException(400, result.get("error", "Bulk delete failed"))
        
        await db.commit()
        
        # Log bulk deletion
        await audit_logs.log_delete(
            db=db,
            user=user,
            entity_type="leads",
            entity_id=None,  # Multiple entities
            description=f"מחיקה קבוצתית של {result['deleted_count']} לידים: {data.ids}",
            request=request,
        )
        
        return result
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))
