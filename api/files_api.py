"""
Files API endpoints.
Handles file uploads, downloads, and management using Cloudflare R2.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from db import get_db
from db.models import File, User
from services.storage import storage_service
from .dependencies import require_entity_access, get_current_user

router = APIRouter()

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


class FileResponse(BaseModel):
    id: int
    filename: str
    content_type: Optional[str]
    size_bytes: Optional[int]
    entity_type: Optional[str]
    entity_id: Optional[int]
    description: Optional[str]
    is_public: bool
    created_at: str


class FileUpdate(BaseModel):
    description: Optional[str] = None
    is_public: Optional[bool] = None


@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    entity_type: Optional[str] = Query(None, description="Entity type (leads, students, expenses, etc)"),
    entity_id: Optional[int] = Query(None, description="Entity ID"),
    description: Optional[str] = Query(None),
    is_public: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file to R2 storage.
    
    Files can be linked to any entity (lead, student, expense, etc) by providing
    entity_type and entity_id parameters.
    """
    # Validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Reset file position for upload
    await file.seek(0)
    
    # Determine folder based on entity
    folder = f"{entity_type}/{entity_id}" if entity_type and entity_id else "general"
    
    try:
        # Upload to storage backend (DB or R2)
        result = await storage_service.upload_file(
            file_data=file.file,
            filename=file.filename or "unnamed",
            folder=folder,
            content_type=file.content_type
        )
    except ValueError as e:
        raise HTTPException(500, f"Storage configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")
    
    # Create database record
    final_entity_id = entity_id if entity_id and entity_id > 0 else None
    
    db_file = File(
        filename=file.filename or "unnamed",
        storage_key=result.get('key'),  # None for DB storage
        file_data=result.get('data'),  # Binary data for DB storage
        content_type=result.get('content_type'),
        size_bytes=result.get('size'),
        entity_type=entity_type if entity_type else None,
        entity_id=final_entity_id,  # 0 is not valid, treat as None
        uploaded_by=user.id if user and user.id else None,
        description=description,
        is_public=is_public,
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "storage_key": db_file.storage_key,
        "url": result.get('url'),
        "size_bytes": db_file.size_bytes,
    }


@router.get("/")
async def list_files(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List files, optionally filtered by entity."""
    query = select(File).order_by(File.created_at.desc()).offset(offset).limit(limit)
    
    if entity_type:
        query = query.where(File.entity_type == entity_type)
    if entity_id:
        query = query.where(File.entity_id == entity_id)
    
    result = await db.execute(query)
    files = result.scalars().all()
    
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "content_type": f.content_type,
            "size_bytes": f.size_bytes,
            "entity_type": f.entity_type,
            "entity_id": f.entity_id,
            "description": f.description,
            "is_public": f.is_public,
            "created_at": str(f.created_at),
        }
        for f in files
    ]


@router.get("/{file_id}")
async def get_file(
    file_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get file metadata by ID."""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(404, "File not found")
    
    return {
        "id": file.id,
        "filename": file.filename,
        "storage_key": file.storage_key,
        "content_type": file.content_type,
        "size_bytes": file.size_bytes,
        "entity_type": file.entity_type,
        "entity_id": file.entity_id,
        "description": file.description,
        "is_public": file.is_public,
        "created_at": str(file.created_at),
    }


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download a file from storage backend.
    For R2: Redirects to presigned URL
    For DB: Returns file directly
    """
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(404, "File not found")
    
    # Check if file is stored in DB
    if file.file_data:
        # Return file directly from DB
        return Response(
            content=file.file_data,
            media_type=file.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file.filename}"'
            }
        )
    
    # File is in R2 - generate presigned URL
    if file.storage_key:
        try:
            url = await storage_service.get_presigned_url(file.storage_key, expires_in=3600)
            if url:
                return RedirectResponse(url=url, status_code=302)
        except Exception as e:
            raise HTTPException(500, f"Could not generate download URL: {str(e)}")
    
    raise HTTPException(404, "File data not found")


@router.patch("/{file_id}")
async def update_file(
    file_id: int,
    data: FileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update file metadata."""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(404, "File not found")
    
    if data.description is not None:
        file.description = data.description
    if data.is_public is not None:
        file.is_public = data.is_public
    
    await db.commit()
    
    return {"id": file.id, "updated": True}


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a file from storage and database."""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(404, "File not found")
    
    # Delete from R2 if stored there
    if file.storage_key:
        try:
            await storage_service.delete_file(file.storage_key)
        except Exception:
            pass  # Continue even if R2 delete fails - file might already be gone
    
    # Delete from database (includes file_data if stored in DB)
    await db.execute(delete(File).where(File.id == file_id))
    await db.commit()
    
    return {"deleted": True}


@router.get("/entity/{entity_type}/{entity_id}")
async def list_entity_files(
    entity_type: str,
    entity_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all files attached to a specific entity."""
    query = select(File).where(
        File.entity_type == entity_type,
        File.entity_id == entity_id
    ).order_by(File.created_at.desc())
    
    result = await db.execute(query)
    files = result.scalars().all()
    
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "content_type": f.content_type,
            "size_bytes": f.size_bytes,
            "description": f.description,
            "is_public": f.is_public,
            "created_at": str(f.created_at),
        }
        for f in files
    ]
