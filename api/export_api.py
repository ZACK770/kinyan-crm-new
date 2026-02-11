from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from db import get_db
from db.models import Lead, Student, Course, Payment, Expense, Attendance, User
from services.export_service import export_service
from api.dependencies import get_current_user

router = APIRouter()


@router.get("/export/leads/csv")
async def export_leads_csv(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export leads to CSV with Hebrew support."""
    if current_user.permission_level < 10:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await session.execute(select(Lead))
    leads = result.scalars().all()
    
    field_mapping = {
        'id': 'מזהה',
        'full_name': 'שם מלא',
        'email': 'דוא"ל',
        'phone': 'טלפון',
        'status': 'סטטוס',
        'source': 'מקור',
        'created_at': 'נוצר ב',
        'updated_at': 'עודכן ב',
    }
    
    exclude_fields = ['_sa_instance_state']
    data = export_service.prepare_export_data(leads, field_mapping, exclude_fields)
    
    csv_content = export_service.export_to_csv(data, "leads.csv")
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )


@router.get("/export/leads/pdf")
async def export_leads_pdf(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export leads to PDF with Hebrew support."""
    if current_user.permission_level < 10:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await session.execute(select(Lead))
    leads = result.scalars().all()
    
    field_mapping = {
        'id': 'מזהה',
        'full_name': 'שם מלא',
        'email': 'דוא"ל',
        'phone': 'טלפון',
        'status': 'סטטוס',
        'source': 'מקור',
    }
    
    exclude_fields = ['_sa_instance_state', 'created_at', 'updated_at']
    data = export_service.prepare_export_data(leads, field_mapping, exclude_fields)
    
    columns = list(field_mapping.values())
    pdf_content = export_service.export_to_pdf(
        data,
        title="דוח לידים",
        columns=columns,
        filename="leads.pdf"
    )
    
    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=leads.pdf"}
    )


@router.get("/export/students/csv")
async def export_students_csv(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export students to CSV with Hebrew support."""
    if current_user.permission_level < 10:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await session.execute(select(Student))
    students = result.scalars().all()
    
    field_mapping = {
        'id': 'מזהה',
        'full_name': 'שם מלא',
        'email': 'דוא"ל',
        'phone': 'טלפון',
        'status': 'סטטוס',
        'created_at': 'נרשם ב',
        'updated_at': 'עודכן ב',
    }
    
    exclude_fields = ['_sa_instance_state']
    data = export_service.prepare_export_data(students, field_mapping, exclude_fields)
    
    csv_content = export_service.export_to_csv(data, "students.csv")
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=students.csv"}
    )


@router.get("/export/students/pdf")
async def export_students_pdf(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export students to PDF with Hebrew support."""
    if current_user.permission_level < 10:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await session.execute(select(Student))
    students = result.scalars().all()
    
    field_mapping = {
        'id': 'מזהה',
        'full_name': 'שם מלא',
        'email': 'דוא"ל',
        'phone': 'טלפון',
        'status': 'סטטוס',
    }
    
    exclude_fields = ['_sa_instance_state', 'created_at', 'updated_at']
    data = export_service.prepare_export_data(students, field_mapping, exclude_fields)
    
    columns = list(field_mapping.values())
    pdf_content = export_service.export_to_pdf(
        data,
        title="דוח תלמידים",
        columns=columns,
        filename="students.pdf"
    )
    
    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=students.pdf"}
    )


@router.get("/export/courses/csv")
async def export_courses_csv(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export courses to CSV with Hebrew support."""
    if current_user.permission_level < 10:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await session.execute(select(Course))
    courses = result.scalars().all()
    
    field_mapping = {
        'id': 'מזהה',
        'name': 'שם קורס',
        'description': 'תיאור',
        'status': 'סטטוס',
        'created_at': 'נוצר ב',
    }
    
    exclude_fields = ['_sa_instance_state']
    data = export_service.prepare_export_data(courses, field_mapping, exclude_fields)
    
    csv_content = export_service.export_to_csv(data, "courses.csv")
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=courses.csv"}
    )


@router.get("/export/courses/pdf")
async def export_courses_pdf(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export courses to PDF with Hebrew support."""
    if current_user.permission_level < 10:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await session.execute(select(Course))
    courses = result.scalars().all()
    
    field_mapping = {
        'id': 'מזהה',
        'name': 'שם קורס',
        'status': 'סטטוס',
    }
    
    exclude_fields = ['_sa_instance_state', 'created_at', 'updated_at', 'description']
    data = export_service.prepare_export_data(courses, field_mapping, exclude_fields)
    
    columns = list(field_mapping.values())
    pdf_content = export_service.export_to_pdf(
        data,
        title="דוח קורסים",
        columns=columns,
        filename="courses.pdf"
    )
    
    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=courses.pdf"}
    )


@router.get("/export/payments/csv")
async def export_payments_csv(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export payments to CSV with Hebrew support."""
    if current_user.permission_level < 10:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await session.execute(select(Payment))
    payments = result.scalars().all()
    
    field_mapping = {
        'id': 'מזהה',
        'amount': 'סכום',
        'status': 'סטטוס',
        'payment_date': 'תאריך תשלום',
        'created_at': 'נוצר ב',
    }
    
    exclude_fields = ['_sa_instance_state']
    data = export_service.prepare_export_data(payments, field_mapping, exclude_fields)
    
    csv_content = export_service.export_to_csv(data, "payments.csv")
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=payments.csv"}
    )


@router.get("/export/payments/pdf")
async def export_payments_pdf(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export payments to PDF with Hebrew support."""
    if current_user.permission_level < 10:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await session.execute(select(Payment))
    payments = result.scalars().all()
    
    field_mapping = {
        'id': 'מזהה',
        'amount': 'סכום',
        'status': 'סטטוס',
        'payment_date': 'תאריך תשלום',
    }
    
    exclude_fields = ['_sa_instance_state', 'created_at', 'updated_at']
    data = export_service.prepare_export_data(payments, field_mapping, exclude_fields)
    
    columns = list(field_mapping.values())
    pdf_content = export_service.export_to_pdf(
        data,
        title="דוח תשלומים",
        columns=columns,
        filename="payments.pdf"
    )
    
    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=payments.pdf"}
    )
