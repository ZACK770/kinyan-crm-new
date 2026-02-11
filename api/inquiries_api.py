"""
Inquiries API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import inquiries as inquiry_svc
from .dependencies import require_entity_access

router = APIRouter()


class InquiryCreate(BaseModel):
    subject: str
    inquiry_type: str  # מייל / דואר קולי / טלפון / אחר
    lead_id: int | None = None
    student_id: int | None = None
    phone: str | None = None
    notes: str | None = None


class InquiryStatusUpdate(BaseModel):
    status: str  # חדש / בטיפול / טופל / סגור
    handled_by: str | None = None


class ResponseCreate(BaseModel):
    author: str | None = None
    content: str | None = None


@router.get("/")
async def list_inquiries(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user = Depends(require_entity_access("inquiries", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await inquiry_svc.list_inquiries(db, status=status, limit=limit, offset=offset)
    return [
        {
            "id": i.id,
            "subject": i.subject,
            "inquiry_type": i.inquiry_type,
            "status": i.status,
            "phone": i.phone,
            "handled_by": i.handled_by,
            "created_at": str(i.created_at),
        }
        for i in items
    ]


@router.post("/")
async def create_inquiry(
    data: InquiryCreate,
    user = Depends(require_entity_access("inquiries", "create")),
    db: AsyncSession = Depends(get_db)
):
    inquiry = await inquiry_svc.create_inquiry(db, **data.model_dump())
    await db.commit()
    return {"id": inquiry.id, "status": inquiry.status}


@router.get("/{inquiry_id}")
async def get_inquiry(
    inquiry_id: int,
    user = Depends(require_entity_access("inquiries", "view")),
    db: AsyncSession = Depends(get_db)
):
    inquiry = await inquiry_svc.get_inquiry_with_responses(db, inquiry_id)
    if not inquiry:
        raise HTTPException(404, "Inquiry not found")
    return {
        "id": inquiry.id,
        "subject": inquiry.subject,
        "inquiry_type": inquiry.inquiry_type,
        "status": inquiry.status,
        "phone": inquiry.phone,
        "handled_by": inquiry.handled_by,
        "notes": inquiry.notes,
        "created_at": str(inquiry.created_at),
        "responses": [
            {
                "id": r.id,
                "author": r.author,
                "content": r.content,
                "created_at": str(r.created_at),
            }
            for r in inquiry.responses
        ],
    }


@router.patch("/{inquiry_id}/status")
async def update_inquiry_status(
    inquiry_id: int,
    data: InquiryStatusUpdate,
    user = Depends(require_entity_access("inquiries", "edit")),
    db: AsyncSession = Depends(get_db)
):
    inquiry = await inquiry_svc.update_inquiry_status(db, inquiry_id, **data.model_dump(exclude_unset=True))
    if not inquiry:
        raise HTTPException(404, "Inquiry not found")
    await db.commit()
    return {"id": inquiry.id, "status": inquiry.status}


@router.post("/{inquiry_id}/responses")
async def add_response(
    inquiry_id: int,
    data: ResponseCreate,
    user = Depends(require_entity_access("inquiries", "edit")),
    db: AsyncSession = Depends(get_db)
):
    response = await inquiry_svc.add_response(db, inquiry_id, **data.model_dump())
    await db.commit()
    return {"id": response.id}
