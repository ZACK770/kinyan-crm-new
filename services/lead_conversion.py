"""
Lead Conversion Service - מעקב המרת לידים לתלמידים
מנהל את תהליך ה-5 שלבים להמרת ליד לתלמיד
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from db.models import Lead, Student, SalesTask, User
from services.audit_logs import log_action


async def check_conversion_complete(lead: Lead) -> bool:
    """
    בדיקה האם כל 5 השלבים הושלמו
    """
    return (
        lead.payment_completed and
        lead.kinyan_signed and
        lead.shipping_details_complete and
        lead.student_chat_added and
        lead.handoff_to_manager and
        lead.handoff_completed
    )


async def update_payment_status(
    session: AsyncSession,
    lead_id: int,
    amount: float,
    method: str,
    reference: Optional[str] = None,
    verified: bool = False,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    עדכון סטטוס תשלום - שלב 1
    """
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    lead.payment_completed = True
    lead.payment_completed_amount = amount
    lead.payment_completed_date = datetime.now(timezone.utc)
    lead.payment_completed_method = method
    lead.payment_reference = reference
    lead.payment_verified = verified
    lead.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    if user_id:
        await log_action(
            session=session,
            user_id=user_id,
            action="lead_payment_completed",
            entity_type="leads",
            entity_id=lead_id,
            details=f"סכום: ₪{amount}, שיטה: {method}"
        )
    
    # בדיקה אם הושלמה המרה
    await check_and_complete_conversion(session, lead, user_id)
    
    return {
        "success": True,
        "payment_completed": True,
        "conversion_progress": await get_conversion_progress(lead)
    }


async def update_kinyan_status(
    session: AsyncSession,
    lead_id: int,
    method: str,
    file_url: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    עדכון סטטוס קניון/תקנון - שלב 2
    """
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    lead.kinyan_signed = True
    lead.kinyan_signed_date = datetime.now(timezone.utc)
    lead.kinyan_method = method
    lead.kinyan_file_url = file_url
    lead.kinyan_notes = notes
    lead.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    if user_id:
        await log_action(
            session=session,
            user_id=user_id,
            action="lead_kinyan_signed",
            entity_type="leads",
            entity_id=lead_id,
            details=f"שיטה: {method}"
        )
    
    await check_and_complete_conversion(session, lead, user_id)
    
    return {
        "success": True,
        "kinyan_signed": True,
        "conversion_progress": await get_conversion_progress(lead)
    }


async def update_shipping_details(
    session: AsyncSession,
    lead_id: int,
    full_address: str,
    city: str,
    postal_code: Optional[str] = None,
    phone: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    עדכון פרטי משלוח - שלב 3
    """
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    lead.shipping_details_complete = True
    lead.shipping_full_address = full_address
    lead.shipping_city = city
    lead.shipping_postal_code = postal_code
    lead.shipping_phone = phone
    lead.shipping_notes = notes
    lead.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    if user_id:
        await log_action(
            session=session,
            user_id=user_id,
            action="lead_shipping_updated",
            entity_type="leads",
            entity_id=lead_id,
            details=f"עיר: {city}"
        )
    
    await check_and_complete_conversion(session, lead, user_id)
    
    return {
        "success": True,
        "shipping_complete": True,
        "conversion_progress": await get_conversion_progress(lead)
    }


async def update_student_chat(
    session: AsyncSession,
    lead_id: int,
    chat_link: str,
    platform: str,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    עדכון הוספה לצ'אט תלמידים - שלב 4
    """
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    lead.student_chat_added = True
    lead.student_chat_link = chat_link
    lead.student_chat_platform = platform
    lead.student_chat_added_date = datetime.now(timezone.utc)
    lead.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    if user_id:
        await log_action(
            session=session,
            user_id=user_id,
            action="lead_chat_added",
            entity_type="leads",
            entity_id=lead_id,
            details=f"פלטפורמה: {platform}"
        )
    
    await check_and_complete_conversion(session, lead, user_id)
    
    return {
        "success": True,
        "chat_added": True,
        "conversion_progress": await get_conversion_progress(lead)
    }


async def handoff_to_class_manager(
    session: AsyncSession,
    lead_id: int,
    manager_id: int,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    העברה למנהל כיתות - שלב 5
    יוצר 2 משימות אוטומטיות למנהל
    """
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    # בדיקה שהמנהל קיים
    manager_result = await session.execute(select(User).where(User.id == manager_id))
    manager = manager_result.scalar_one_or_none()
    
    if not manager:
        return {"success": False, "error": "Manager not found"}
    
    lead.handoff_to_manager = True
    lead.handoff_date = datetime.now(timezone.utc)
    lead.handoff_manager_id = manager_id
    lead.updated_at = datetime.now(timezone.utc)
    
    # יצירת משימה 1: אישור קבלת משלוח
    task1 = SalesTask(
        title=f"אשר קבלת חומרי לימוד/משלוח - {lead.full_name}",
        description=f"וודא שהתלמיד {lead.full_name} (טלפון: {lead.phone}) קיבל את חומרי הלימוד/המשלוח",
        task_type="class_management",
        assigned_to_user_id=manager_id,
        lead_id=lead_id,
        auto_created=True,
        parent_lead_conversion=True,
        priority=2,
        status="חדש"
    )
    session.add(task1)
    
    # יצירת משימה 2: וידוא הצטרפות לצ'אט
    task2 = SalesTask(
        title=f"וודא הצטרפות לצ'אט תלמידים - {lead.full_name}",
        description=f"וודא שהתלמיד {lead.full_name} הצטרף לקבוצת התלמידים ב-{lead.student_chat_platform or 'WhatsApp'}",
        task_type="class_management",
        assigned_to_user_id=manager_id,
        lead_id=lead_id,
        auto_created=True,
        parent_lead_conversion=True,
        priority=2,
        status="חדש"
    )
    session.add(task2)
    
    await session.commit()
    
    if user_id:
        await log_action(
            session=session,
            user_id=user_id,
            action="lead_handoff_to_manager",
            entity_type="leads",
            entity_id=lead_id,
            details=f"הועבר למנהל: {manager.full_name}"
        )
    
    await check_and_complete_conversion(session, lead, user_id)
    
    return {
        "success": True,
        "handoff_complete": True,
        "tasks_created": 2,
        "manager_name": manager.full_name,
        "conversion_progress": await get_conversion_progress(lead)
    }


async def complete_manager_task(
    session: AsyncSession,
    task_id: int,
    user_id: int
) -> Dict[str, Any]:
    """
    סימון משימת מנהל כהושלמה
    אם שתי המשימות הושלמו - מעדכן handoff_completed
    """
    result = await session.execute(select(SalesTask).where(SalesTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        return {"success": False, "error": "Task not found"}
    
    task.status = "הושלם"
    task.completed_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    # בדיקה אם כל המשימות של הליד הושלמו
    if task.lead_id and task.parent_lead_conversion:
        lead_result = await session.execute(select(Lead).where(Lead.id == task.lead_id))
        lead = lead_result.scalar_one_or_none()
        
        if lead:
            # בדיקה אם כל המשימות הקשורות להמרה הושלמו
            tasks_result = await session.execute(
                select(SalesTask).where(
                    and_(
                        SalesTask.lead_id == task.lead_id,
                        SalesTask.parent_lead_conversion == True,
                        SalesTask.status != "הושלם"
                    )
                )
            )
            pending_tasks = tasks_result.scalars().all()
            
            if not pending_tasks:
                lead.handoff_completed = True
                lead.handoff_completed_date = datetime.now(timezone.utc)
                await session.commit()
                
                await log_action(
                    session=session,
                    user_id=user_id,
                    action="lead_handoff_completed",
                    entity_type="leads",
                    entity_id=lead.id,
                    details="כל משימות המנהל הושלמו"
                )
                
                # בדיקה אם הושלמה המרה
                await check_and_complete_conversion(session, lead, user_id)
    
    return {"success": True, "task_completed": True}


async def check_and_complete_conversion(
    session: AsyncSession,
    lead: Lead,
    user_id: Optional[int] = None
) -> bool:
    """
    בדיקה והשלמת המרה אוטומטית אם כל השלבים הושלמו
    """
    if await check_conversion_complete(lead):
        if not lead.conversion_checklist_complete:
            lead.conversion_checklist_complete = True
            lead.conversion_completed_at = datetime.now(timezone.utc)
            lead.conversion_completed_by_id = user_id
            lead.status = "נסלק"
            
            # יצירת תלמיד מהליד
            await convert_lead_to_student(session, lead)
            
            await session.commit()
            
            if user_id:
                await log_action(
                    session=session,
                    user_id=user_id,
                    action="lead_converted_to_student",
                    entity_type="leads",
                    entity_id=lead.id,
                    details="המרה אוטומטית לתלמיד הושלמה"
                )
            
            return True
    
    return False


async def convert_lead_to_student(session: AsyncSession, lead: Lead) -> Student:
    """
    המרת ליד לתלמיד
    """
    if lead.student_id:
        result = await session.execute(select(Student).where(Student.id == lead.student_id))
        existing_student = result.scalar_one_or_none()
        if existing_student:
            return existing_student
    
    student = Student(
        full_name=lead.full_name,
        id_number=lead.id_number,
        phone=lead.phone,
        phone2=lead.phone2,
        address=lead.shipping_full_address or lead.address,
        city=lead.shipping_city or lead.city,
        email=lead.email,
        notes=lead.notes,
        status="תלמיד פעיל",
        approved_terms=lead.kinyan_signed,
        lead_id=lead.id,
        total_price=lead.payment_completed_amount,
        total_paid=lead.payment_completed_amount if lead.payment_verified else 0,
        payment_status="שולם" if lead.payment_verified else "חייב",
        shipping_status="ממתין"
    )
    
    session.add(student)
    await session.flush()
    
    lead.student_id = student.id
    
    return student


async def get_conversion_progress(lead: Lead) -> Dict[str, Any]:
    """
    קבלת התקדמות המרה
    """
    steps = {
        "payment": lead.payment_completed,
        "kinyan": lead.kinyan_signed,
        "shipping": lead.shipping_details_complete,
        "chat": lead.student_chat_added,
        "handoff": lead.handoff_to_manager and lead.handoff_completed
    }
    
    completed = sum(steps.values())
    total = len(steps)
    percentage = int((completed / total) * 100)
    
    return {
        "steps": steps,
        "completed": completed,
        "total": total,
        "percentage": percentage,
        "conversion_complete": lead.conversion_checklist_complete
    }


async def get_conversion_metrics(
    session: AsyncSession,
    salesperson_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    מדדי המרה לאיש מכירות
    """
    filters = []
    
    if salesperson_id:
        filters.append(Lead.salesperson_id == salesperson_id)
    
    if start_date:
        filters.append(Lead.conversion_completed_at >= start_date)
    
    if end_date:
        filters.append(Lead.conversion_completed_at <= end_date)
    
    # המרות שהושלמו
    conversions_query = select(func.count(Lead.id)).where(
        and_(Lead.conversion_checklist_complete == True, *filters)
    )
    conversions_result = await session.execute(conversions_query)
    total_conversions = conversions_result.scalar() or 0
    
    # בתהליך המרה (תשלום בוצע אבל לא הושלם)
    in_progress_query = select(func.count(Lead.id)).where(
        and_(
            Lead.payment_completed == True,
            Lead.conversion_checklist_complete == False,
            *([Lead.salesperson_id == salesperson_id] if salesperson_id else [])
        )
    )
    in_progress_result = await session.execute(in_progress_query)
    in_progress = in_progress_result.scalar() or 0
    
    # זמן ממוצע להמרה
    avg_time_query = select(
        func.avg(
            func.extract('epoch', Lead.conversion_completed_at - Lead.payment_completed_date) / 86400
        )
    ).where(
        and_(
            Lead.conversion_checklist_complete == True,
            Lead.payment_completed_date.isnot(None),
            *filters
        )
    )
    avg_time_result = await session.execute(avg_time_query)
    avg_days = avg_time_result.scalar() or 0
    
    # לידים שדורשים תשומת לב (תשלום בוצע לפני יותר מ-3 ימים)
    attention_query = select(Lead).where(
        and_(
            Lead.payment_completed == True,
            Lead.conversion_checklist_complete == False,
            Lead.payment_completed_date < datetime.now(),
            *([Lead.salesperson_id == salesperson_id] if salesperson_id else [])
        )
    ).limit(10)
    attention_result = await session.execute(attention_query)
    needs_attention = attention_result.scalars().all()
    
    return {
        "total_conversions": total_conversions,
        "in_progress": in_progress,
        "avg_conversion_days": round(avg_days, 1),
        "needs_attention": [
            {
                "id": lead.id,
                "name": lead.full_name,
                "phone": lead.phone,
                "missing_steps": get_missing_steps(lead),
                "days_since_payment": (datetime.now() - lead.payment_completed_date).days if lead.payment_completed_date else 0
            }
            for lead in needs_attention
        ]
    }


def get_missing_steps(lead: Lead) -> List[str]:
    """
    קבלת רשימת שלבים חסרים
    """
    missing = []
    
    if not lead.payment_completed:
        missing.append("תשלום")
    if not lead.kinyan_signed:
        missing.append("קניון")
    if not lead.shipping_details_complete:
        missing.append("פרטי משלוח")
    if not lead.student_chat_added:
        missing.append("צ'אט תלמידים")
    if not lead.handoff_to_manager:
        missing.append("העברה למנהל")
    elif not lead.handoff_completed:
        missing.append("אישור מנהל")
    
    return missing
