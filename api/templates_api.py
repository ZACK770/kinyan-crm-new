"""
Email Templates API — CRUD for email templates with attachments.
Prefix: /api/templates
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional, List

from db import get_db
from db.models import EmailTemplate, File, User
from services.storage import storage_service
from .dependencies import require_entity_access, get_current_user

router = APIRouter(tags=["templates"])


# ── Schemas ──────────────────────────────────────────
class TemplateCreate(BaseModel):
    name: str
    subject: str
    body_html: str
    category: Optional[str] = None
    track_type: Optional[str] = None
    is_active: bool = True


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    category: Optional[str] = None
    track_type: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    body_html: str
    category: Optional[str]
    track_type: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    attachments: List[dict] = []


# ── List templates ────────────────────────────────────
@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None),
    track_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all email templates with optional filters."""
    query = select(EmailTemplate).order_by(EmailTemplate.name)
    
    if category:
        query = query.where(EmailTemplate.category == category)
    if track_type:
        query = query.where(EmailTemplate.track_type == track_type)
    if is_active is not None:
        query = query.where(EmailTemplate.is_active == is_active)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    # Get attachments for each template
    response = []
    for t in templates:
        attachments_query = select(File).where(
            File.entity_type == "templates",
            File.entity_id == t.id
        )
        attachments_result = await db.execute(attachments_query)
        attachments = attachments_result.scalars().all()
        
        response.append({
            "id": t.id,
            "name": t.name,
            "subject": t.subject,
            "body_html": t.body_html,
            "category": t.category,
            "track_type": t.track_type,
            "is_active": t.is_active,
            "created_at": str(t.created_at),
            "updated_at": str(t.updated_at),
            "attachments": [
                {
                    "id": a.id,
                    "filename": a.filename,
                    "size_bytes": a.size_bytes,
                    "content_type": a.content_type,
                }
                for a in attachments
            ]
        })
    
    return response


# ── Get single template ───────────────────────────────
@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific template by ID with attachments."""
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(404, "תבנית לא נמצאה")
    
    # Get attachments
    attachments_query = select(File).where(
        File.entity_type == "templates",
        File.entity_id == template_id
    )
    attachments_result = await db.execute(attachments_query)
    attachments = attachments_result.scalars().all()
    
    return {
        "id": template.id,
        "name": template.name,
        "subject": template.subject,
        "body_html": template.body_html,
        "category": template.category,
        "track_type": template.track_type,
        "is_active": template.is_active,
        "created_at": str(template.created_at),
        "updated_at": str(template.updated_at),
        "attachments": [
            {
                "id": a.id,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "content_type": a.content_type,
            }
            for a in attachments
        ]
    }


# ── Create template ───────────────────────────────────
@router.post("/", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    user: User = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new email template."""
    template = EmailTemplate(
        name=data.name,
        subject=data.subject,
        body_html=data.body_html,
        category=data.category,
        track_type=data.track_type,
        is_active=data.is_active,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return {
        "id": template.id,
        "name": template.name,
        "subject": template.subject,
        "body_html": template.body_html,
        "category": template.category,
        "track_type": template.track_type,
        "is_active": template.is_active,
        "created_at": str(template.created_at),
        "updated_at": str(template.updated_at),
        "attachments": []
    }


# ── Update template ───────────────────────────────────
@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    user: User = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing template."""
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(404, "תבנית לא נמצאה")
    
    if data.name is not None:
        template.name = data.name
    if data.subject is not None:
        template.subject = data.subject
    if data.body_html is not None:
        template.body_html = data.body_html
    if data.category is not None:
        template.category = data.category
    if data.track_type is not None:
        template.track_type = data.track_type
    if data.is_active is not None:
        template.is_active = data.is_active
    
    await db.commit()
    await db.refresh(template)
    
    # Get attachments
    attachments_query = select(File).where(
        File.entity_type == "templates",
        File.entity_id == template_id
    )
    attachments_result = await db.execute(attachments_query)
    attachments = attachments_result.scalars().all()
    
    return {
        "id": template.id,
        "name": template.name,
        "subject": template.subject,
        "body_html": template.body_html,
        "category": template.category,
        "track_type": template.track_type,
        "is_active": template.is_active,
        "created_at": str(template.created_at),
        "updated_at": str(template.updated_at),
        "attachments": [
            {
                "id": a.id,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "content_type": a.content_type,
            }
            for a in attachments
        ]
    }


# ── Delete template ───────────────────────────────────
@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    user: User = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a template and its attachments."""
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(404, "תבנית לא נמצאה")
    
    # Delete attachments from R2 and DB
    attachments_query = select(File).where(
        File.entity_type == "templates",
        File.entity_id == template_id
    )
    attachments_result = await db.execute(attachments_query)
    attachments = attachments_result.scalars().all()
    
    for attachment in attachments:
        try:
            await storage_service.delete_file(attachment.storage_key)
        except Exception:
            pass
    
    await db.execute(delete(File).where(
        File.entity_type == "templates",
        File.entity_id == template_id
    ))
    
    # Delete template
    await db.execute(delete(EmailTemplate).where(EmailTemplate.id == template_id))
    await db.commit()
    
    return {"deleted": True}


# ── Add attachment to template ────────────────────────
@router.post("/{template_id}/attachments")
async def add_template_attachment(
    template_id: int,
    file: UploadFile = FastAPIFile(...),
    user: User = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Upload and attach a file to a template."""
    # Verify template exists
    result = await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(404, "תבנית לא נמצאה")
    
    # Upload to R2
    try:
        upload_result = await storage_service.upload_file(
            file_data=file.file,
            filename=file.filename or "unnamed",
            folder=f"templates/{template_id}",
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(500, f"העלאת הקובץ נכשלה: {str(e)}")
    
    # Create file record
    db_file = File(
        filename=file.filename or "unnamed",
        storage_key=upload_result['key'],
        content_type=upload_result.get('content_type'),
        size_bytes=upload_result.get('size'),
        entity_type="templates",
        entity_id=template_id,
        uploaded_by=user.id,
        is_public=False,
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "size_bytes": db_file.size_bytes,
        "content_type": db_file.content_type,
    }


# ── Remove attachment from template ───────────────────
@router.delete("/{template_id}/attachments/{file_id}")
async def remove_template_attachment(
    template_id: int,
    file_id: int,
    user: User = Depends(require_entity_access("leads", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Remove an attachment from a template."""
    result = await db.execute(select(File).where(
        File.id == file_id,
        File.entity_type == "templates",
        File.entity_id == template_id
    ))
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(404, "קובץ לא נמצא")
    
    # Delete from R2
    try:
        await storage_service.delete_file(file.storage_key)
    except Exception:
        pass
    
    # Delete from DB
    await db.execute(delete(File).where(File.id == file_id))
    await db.commit()
    
    return {"deleted": True}
