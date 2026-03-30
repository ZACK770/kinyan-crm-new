from datetime import date, datetime
from typing import Optional
import secrets
import string

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import ExamDate, Exam, Examinee, ExamRegistration, ExamDateExam


async def get_upcoming_exam_dates(db: AsyncSession) -> list[dict]:
    """Get upcoming active exam dates with available exams."""
    today = date.today()
    
    stmt = (
        select(ExamDate)
        .options(selectinload(ExamDate.exams).selectinload(Exam.course))
        .where(
            and_(
                ExamDate.date >= today,
                ExamDate.is_active == True
            )
        )
        .order_by(ExamDate.date)
    )
    
    result = await db.execute(stmt)
    exam_dates = result.scalars().all()
    
    items = []
    for ed in exam_dates:
        # Only include exam dates that have exams assigned
        if not ed.exams:
            continue
            
        exams_data = []
        for exam in ed.exams:
            exams_data.append({
                "exam_id": exam.id,
                "exam_name": exam.name,
                "exam_type": exam.exam_type,
                "course_id": exam.course_id,
                "course_name": exam.course.name if exam.course else None,
            })
        
        items.append({
            "exam_date_id": ed.id,
            "date": str(ed.date),
            "description": ed.description,
            "max_registrations": ed.max_registrations,
            "exams": exams_data,
        })
    
    return items


async def create_exam_registration(
    db: AsyncSession,
    exam_date_id: int,
    exam_id: int,
    phone: str,
    name: Optional[str] = None,
    notes: Optional[str] = None
) -> dict:
    """Create a new exam registration for an examinee."""
    
    # Get or create examinee
    stmt = select(Examinee).where(Examinee.phone == phone)
    result = await db.execute(stmt)
    examinee = result.scalar_one_or_none()
    
    if not examinee:
        # Auto-create examinee for registration
        examinee = Examinee(
            name=name or phone,
            phone=phone,
            is_verified=False  # Can be verified later
        )
        db.add(examinee)
        await db.flush()
    
    # Check if already registered
    existing_stmt = select(ExamRegistration).where(
        and_(
            ExamRegistration.exam_date_id == exam_date_id,
            ExamRegistration.exam_id == exam_id,
            ExamRegistration.examinee_id == examinee.id,
            ExamRegistration.status == "registered"
        )
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise ValueError("כבר רשום לבחינה זו")
    
    # Verify exam date and exam exist and are linked
    exam_date_stmt = select(ExamDate).where(ExamDate.id == exam_date_id)
    exam_date_result = await db.execute(exam_date_stmt)
    exam_date = exam_date_result.scalar_one_or_none()
    
    if not exam_date or not exam_date.is_active:
        raise ValueError("תאריך בחינה לא פעיל")
    
    # Check if exam is assigned to this date
    exam_link_stmt = select(ExamDateExam).where(
        and_(
            ExamDateExam.exam_date_id == exam_date_id,
            ExamDateExam.exam_id == exam_id
        )
    )
    exam_link_result = await db.execute(exam_link_stmt)
    if not exam_link_result.scalar_one_or_none():
        raise ValueError("בחינה לא משויכת לתאריך זה")
    
    # Check capacity
    if exam_date.max_registrations:
        current_registrations_stmt = select(func.count(ExamRegistration.id)).where(
            and_(
                ExamRegistration.exam_date_id == exam_date_id,
                ExamRegistration.status == "registered"
            )
        )
        current_count = await db.scalar(current_registrations_stmt)
        if current_count >= exam_date.max_registrations:
            raise ValueError("אין מקום פנוי בתאריך זה")
    
    # Generate unique registration code
    def generate_code():
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    registration_code = generate_code()
    # Ensure uniqueness
    while await db.scalar(select(ExamRegistration.id).where(ExamRegistration.registration_code == registration_code)):
        registration_code = generate_code()
    
    # Create registration
    registration = ExamRegistration(
        exam_date_id=exam_date_id,
        exam_id=exam_id,
        examinee_id=examinee.id,
        status="registered",
        registration_code=registration_code,
        notes=notes
    )
    
    db.add(registration)
    await db.commit()
    await db.refresh(registration)
    
    # Load related data for response
    await db.refresh(registration, ["exam_date", "exam", "examinee"])
    
    return {
        "registration_id": registration.id,
        "registration_code": registration.registration_code,
        "exam_date": str(registration.exam_date.date),
        "exam_name": registration.exam.name,
        "examinee_name": registration.examinee.name,
        "examinee_phone": registration.examinee.phone,
        "status": registration.status,
        "created_at": str(registration.created_at),
    }


async def get_examinee_registrations(db: AsyncSession, phone: str) -> list[dict]:
    """Get all registrations for an examinee by phone."""
    
    # Find examinee
    stmt = select(Examinee).where(Examinee.phone == phone)
    result = await db.execute(stmt)
    examinee = result.scalar_one_or_none()
    
    if not examinee:
        return []
    
    # Get registrations
    reg_stmt = (
        select(ExamRegistration)
        .options(
            selectinload(ExamRegistration.exam_date),
            selectinload(ExamRegistration.exam).selectinload(Exam.course)
        )
        .where(ExamRegistration.examinee_id == examinee.id)
        .order_by(ExamRegistration.created_at.desc())
    )
    
    reg_result = await db.execute(reg_stmt)
    registrations = reg_result.scalars().all()
    
    items = []
    for reg in registrations:
        items.append({
            "registration_id": reg.id,
            "registration_code": reg.registration_code,
            "exam_date": str(reg.exam_date.date),
            "exam_name": reg.exam.name,
            "exam_type": reg.exam.exam_type,
            "course_name": reg.exam.course.name if reg.exam.course else None,
            "status": reg.status,
            "notes": reg.notes,
            "created_at": str(reg.created_at),
        })
    
    return items
