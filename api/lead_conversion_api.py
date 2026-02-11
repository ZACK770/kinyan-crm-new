"""
Lead Conversion API - ניהול תהליך המרת לידים לתלמידים
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from db import get_db
from services.auth import get_current_user, require_permission
from services.lead_conversion import (
    update_payment_status,
    update_kinyan_status,
    update_shipping_details,
    update_student_chat,
    handoff_to_class_manager,
    complete_manager_task,
    get_conversion_progress,
    get_conversion_metrics
)
from db.models import User, Lead
from sqlalchemy import select

router = APIRouter(prefix="/api/leads", tags=["lead_conversion"])


# ============================================================
# Request Models
# ============================================================

class PaymentUpdateRequest(BaseModel):
    amount: float = Field(..., gt=0, description="סכום התשלום")
    method: str = Field(..., description="שיטת תשלום: אשראי/העברה/מזומן")
    reference: Optional[str] = Field(None, description="אסמכתא")
    verified: bool = Field(False, description="אושר ע\"י נדרים פלוס")


class KinyanUpdateRequest(BaseModel):
    method: str = Field(..., description="שיטת אישור: PDF במייל/אישור טלפוני/IVR/חתימה דיגיטלית")
    file_url: Optional[str] = Field(None, description="קישור לקובץ PDF")
    notes: Optional[str] = Field(None, description="הערות")


class ShippingUpdateRequest(BaseModel):
    full_address: str = Field(..., description="כתובת מלאה")
    city: str = Field(..., description="עיר")
    postal_code: Optional[str] = Field(None, description="מיקוד")
    phone: Optional[str] = Field(None, description="טלפון למשלוח")
    notes: Optional[str] = Field(None, description="הערות למשלוח")


class StudentChatUpdateRequest(BaseModel):
    chat_link: str = Field(..., description="לינק לקבוצת תלמידים")
    platform: str = Field(..., description="פלטפורמה: WhatsApp/Telegram/Discord")


class HandoffRequest(BaseModel):
    manager_id: int = Field(..., description="ID של מנהל הכיתות")


# ============================================================
# Endpoints
# ============================================================

@router.post("/{lead_id}/conversion/payment")
async def update_lead_payment(
    lead_id: int,
    data: PaymentUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads", "edit"))
):
    """
    עדכון סטטוס תשלום - שלב 1 בתהליך ההמרה
    """
    result = await update_payment_status(
        session=session,
        lead_id=lead_id,
        amount=data.amount,
        method=data.method,
        reference=data.reference,
        verified=data.verified,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to update payment"))
    
    return result


@router.post("/{lead_id}/conversion/kinyan")
async def update_lead_kinyan(
    lead_id: int,
    data: KinyanUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads", "edit"))
):
    """
    עדכון סטטוס קניון/תקנון - שלב 2 בתהליך ההמרה
    """
    result = await update_kinyan_status(
        session=session,
        lead_id=lead_id,
        method=data.method,
        file_url=data.file_url,
        notes=data.notes,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to update kinyan"))
    
    return result


@router.put("/{lead_id}/conversion/shipping")
async def update_lead_shipping(
    lead_id: int,
    data: ShippingUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads", "edit"))
):
    """
    עדכון פרטי משלוח - שלב 3 בתהליך ההמרה
    """
    result = await update_shipping_details(
        session=session,
        lead_id=lead_id,
        full_address=data.full_address,
        city=data.city,
        postal_code=data.postal_code,
        phone=data.phone,
        notes=data.notes,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to update shipping"))
    
    return result


@router.post("/{lead_id}/conversion/student-chat")
async def update_lead_student_chat(
    lead_id: int,
    data: StudentChatUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads", "edit"))
):
    """
    עדכון הוספה לצ'אט תלמידים - שלב 4 בתהליך ההמרה
    """
    result = await update_student_chat(
        session=session,
        lead_id=lead_id,
        chat_link=data.chat_link,
        platform=data.platform,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to update student chat"))
    
    return result


@router.post("/{lead_id}/conversion/handoff")
async def handoff_lead_to_manager(
    lead_id: int,
    data: HandoffRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads", "edit"))
):
    """
    העברה למנהל כיתות - שלב 5 בתהליך ההמרה
    יוצר אוטומטית 2 משימות למנהל הכיתות
    """
    result = await handoff_to_class_manager(
        session=session,
        lead_id=lead_id,
        manager_id=data.manager_id,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to handoff to manager"))
    
    return result


@router.get("/{lead_id}/conversion/status")
async def get_lead_conversion_status(
    lead_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads", "view"))
):
    """
    קבלת סטטוס המרה של ליד
    """
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    progress = await get_conversion_progress(lead)
    
    return {
        "lead_id": lead_id,
        "lead_name": lead.full_name,
        "status": lead.status,
        "conversion_progress": progress,
        "details": {
            "payment": {
                "completed": lead.payment_completed,
                "amount": float(lead.payment_completed_amount) if lead.payment_completed_amount else None,
                "date": lead.payment_completed_date.isoformat() if lead.payment_completed_date else None,
                "method": lead.payment_completed_method,
                "verified": lead.payment_verified
            },
            "kinyan": {
                "signed": lead.kinyan_signed,
                "date": lead.kinyan_signed_date.isoformat() if lead.kinyan_signed_date else None,
                "method": lead.kinyan_method,
                "file_url": lead.kinyan_file_url
            },
            "shipping": {
                "complete": lead.shipping_details_complete,
                "address": lead.shipping_full_address,
                "city": lead.shipping_city,
                "phone": lead.shipping_phone
            },
            "student_chat": {
                "added": lead.student_chat_added,
                "platform": lead.student_chat_platform,
                "link": lead.student_chat_link,
                "date": lead.student_chat_added_date.isoformat() if lead.student_chat_added_date else None
            },
            "handoff": {
                "to_manager": lead.handoff_to_manager,
                "completed": lead.handoff_completed,
                "manager_id": lead.handoff_manager_id,
                "date": lead.handoff_date.isoformat() if lead.handoff_date else None
            }
        }
    }


@router.get("/conversion/metrics")
async def get_sales_conversion_metrics(
    salesperson_id: Optional[int] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    מדדי המרה לאיש מכירות
    אם לא מועבר salesperson_id, מחזיר מדדים של המשתמש הנוכחי
    """
    # אם לא צוין salesperson_id, ננסה למצוא את ה-salesperson של המשתמש
    if not salesperson_id:
        from db.models import Salesperson
        result = await session.execute(
            select(Salesperson).where(Salesperson.email == current_user.email)
        )
        salesperson = result.scalar_one_or_none()
        if salesperson:
            salesperson_id = salesperson.id
    
    metrics = await get_conversion_metrics(
        session=session,
        salesperson_id=salesperson_id
    )
    
    return metrics


@router.post("/tasks/{task_id}/complete")
async def complete_class_manager_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    סימון משימת מנהל כיתות כהושלמה
    """
    from services.lead_conversion import complete_manager_task
    
    result = await complete_manager_task(
        session=session,
        task_id=task_id,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to complete task"))
    
    return result


@router.get("/class-manager/tasks")
async def get_class_manager_tasks(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    קבלת רשימת משימות למנהל כיתות
    """
    from db.models import SalesTask, Lead
    from sqlalchemy import and_
    
    # בדיקה שהמשתמש הוא מנהל כיתות
    if current_user.role_name != "class_manager" and current_user.role_name != "admin":
        raise HTTPException(status_code=403, detail="Access denied - class manager role required")
    
    filters = [
        SalesTask.assigned_to_user_id == current_user.id,
        SalesTask.task_type == "class_management"
    ]
    
    if status:
        filters.append(SalesTask.status == status)
    
    result = await session.execute(
        select(SalesTask, Lead)
        .outerjoin(Lead, SalesTask.lead_id == Lead.id)
        .where(and_(*filters))
        .order_by(SalesTask.priority.desc(), SalesTask.created_at.desc())
    )
    
    tasks_data = []
    for task, lead in result.all():
        tasks_data.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "lead": {
                "id": lead.id,
                "name": lead.full_name,
                "phone": lead.phone,
                "status": lead.status
            } if lead else None
        })
    
    return {
        "total": len(tasks_data),
        "tasks": tasks_data
    }
