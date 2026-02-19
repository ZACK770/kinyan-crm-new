"""
Popup Announcements API — הודעות פופ-אפ מתפרצות לצוות
Prefix: /api/popups
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import User, PopupAnnouncement, PopupDismissal
from api.dependencies import get_current_user, require_permission

router = APIRouter()


# ── Pydantic schemas ─────────────────────────────────

class PopupCreate(BaseModel):
    title: str
    body: Optional[str] = None
    image_url: Optional[str] = None
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None
    theme: str = "default"
    animation: str = "slideUp"
    target_audience: str = "all"
    min_permission_level: int = 0
    is_active: bool = True
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    show_count: int = 1
    is_template: bool = False
    priority: int = 0


class PopupUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None
    theme: Optional[str] = None
    animation: Optional[str] = None
    target_audience: Optional[str] = None
    min_permission_level: Optional[int] = None
    is_active: Optional[bool] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    show_count: Optional[int] = None
    is_template: Optional[bool] = None
    priority: Optional[int] = None


IL_TZ = ZoneInfo("Asia/Jerusalem")


def _parse_dt(val: Optional[str]) -> Optional[datetime]:
    """Parse datetime string from frontend (datetime-local = Israel time) → UTC-aware."""
    if not val:
        return None
    try:
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            # datetime-local input has no timezone — treat as Israel time
            dt = dt.replace(tzinfo=IL_TZ)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _dt_to_il(dt: Optional[datetime]) -> Optional[str]:
    """Convert a DB datetime to Israel-time ISO string for the frontend."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IL_TZ).isoformat()


def _serialize(ann: PopupAnnouncement, dismiss_count: int = 0) -> dict:
    return {
        "id": ann.id,
        "title": ann.title,
        "body": ann.body,
        "image_url": ann.image_url,
        "cta_text": ann.cta_text,
        "cta_link": ann.cta_link,
        "theme": ann.theme,
        "animation": ann.animation,
        "target_audience": ann.target_audience,
        "min_permission_level": ann.min_permission_level,
        "is_active": ann.is_active,
        "start_at": _dt_to_il(ann.start_at),
        "end_at": _dt_to_il(ann.end_at),
        "show_count": ann.show_count,
        "is_template": ann.is_template,
        "priority": ann.priority,
        "created_by_user_id": ann.created_by_user_id,
        "created_at": str(ann.created_at) if ann.created_at else None,
        "updated_at": str(ann.updated_at) if ann.updated_at else None,
        "dismiss_count": dismiss_count,
    }


# ── Admin CRUD (manager+) ────────────────────────────

@router.get("/")
async def list_announcements(
    include_templates: bool = False,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """List all announcements (manager+). Optionally include templates."""
    stmt = select(PopupAnnouncement).order_by(PopupAnnouncement.created_at.desc())
    if not include_templates:
        stmt = stmt.where(PopupAnnouncement.is_template == False)  # noqa: E712
    result = await db.execute(stmt)
    announcements = result.scalars().all()

    items = []
    for ann in announcements:
        count_result = await db.execute(
            select(func.count(PopupDismissal.id)).where(PopupDismissal.announcement_id == ann.id)
        )
        dismiss_count = count_result.scalar() or 0
        items.append(_serialize(ann, dismiss_count))
    return items


@router.get("/templates")
async def list_templates(
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """List saved templates."""
    stmt = (
        select(PopupAnnouncement)
        .where(PopupAnnouncement.is_template == True)  # noqa: E712
        .order_by(PopupAnnouncement.created_at.desc())
    )
    result = await db.execute(stmt)
    return [_serialize(ann) for ann in result.scalars().all()]


@router.post("/")
async def create_announcement(
    data: PopupCreate,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new popup announcement."""
    ann = PopupAnnouncement(
        title=data.title,
        body=data.body,
        image_url=data.image_url,
        cta_text=data.cta_text,
        cta_link=data.cta_link,
        theme=data.theme,
        animation=data.animation,
        target_audience=data.target_audience,
        min_permission_level=data.min_permission_level,
        is_active=data.is_active,
        start_at=_parse_dt(data.start_at),
        end_at=_parse_dt(data.end_at),
        show_count=data.show_count,
        is_template=data.is_template,
        priority=data.priority,
        created_by_user_id=user.id,
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return _serialize(ann)


@router.patch("/{popup_id}")
async def update_announcement(
    popup_id: int,
    data: PopupUpdate,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing announcement."""
    ann = await db.get(PopupAnnouncement, popup_id)
    if not ann:
        raise HTTPException(status_code=404, detail="הודעה לא נמצאה")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        if key in ("start_at", "end_at"):
            setattr(ann, key, _parse_dt(val))
        else:
            setattr(ann, key, val)

    await db.commit()
    await db.refresh(ann)
    return _serialize(ann)


@router.delete("/{popup_id}")
async def delete_announcement(
    popup_id: int,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an announcement."""
    ann = await db.get(PopupAnnouncement, popup_id)
    if not ann:
        raise HTTPException(status_code=404, detail="הודעה לא נמצאה")
    await db.delete(ann)
    await db.commit()
    return {"ok": True}


@router.post("/{popup_id}/duplicate")
async def duplicate_announcement(
    popup_id: int,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Duplicate an announcement (useful for templates)."""
    source = await db.get(PopupAnnouncement, popup_id)
    if not source:
        raise HTTPException(status_code=404, detail="הודעה לא נמצאה")

    new_ann = PopupAnnouncement(
        title=f"{source.title} (עותק)",
        body=source.body,
        image_url=source.image_url,
        cta_text=source.cta_text,
        cta_link=source.cta_link,
        theme=source.theme,
        animation=source.animation,
        target_audience=source.target_audience,
        min_permission_level=source.min_permission_level,
        is_active=False,
        start_at=None,
        end_at=None,
        show_count=source.show_count,
        is_template=source.is_template,
        priority=source.priority,
        created_by_user_id=user.id,
    )
    db.add(new_ann)
    await db.commit()
    await db.refresh(new_ann)
    return _serialize(new_ann)


# ── User-facing endpoints ────────────────────────────

def _ensure_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Make sure a datetime is timezone-aware (assume UTC if naive)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/active")
async def get_active_popups(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get popups that should be shown to the current user.
    Called by frontend on load and periodically.
    """
    now = datetime.now(timezone.utc)

    # Fetch all active non-template popups; time filtering done in Python
    # to safely handle naive/aware datetime mismatches in existing DB data
    stmt = (
        select(PopupAnnouncement)
        .where(
            PopupAnnouncement.is_active == True,  # noqa: E712
            PopupAnnouncement.is_template == False,  # noqa: E712
        )
        .order_by(PopupAnnouncement.priority.desc(), PopupAnnouncement.created_at.desc())
    )
    result = await db.execute(stmt)
    announcements = result.scalars().all()

    visible = []
    for ann in announcements:
        # Check schedule window (handle naive datetimes gracefully)
        start = _ensure_aware(ann.start_at)
        end = _ensure_aware(ann.end_at)
        if start and start > now:
            continue
        if end and end < now:
            continue

        # Check audience targeting
        if ann.min_permission_level > user.permission_level:
            continue
        if ann.target_audience != "all":
            if ann.target_audience == "salesperson" and user.role_name not in ("salesperson", "manager", "admin"):
                continue
            if ann.target_audience == "manager" and user.role_name not in ("manager", "admin"):
                continue
            if ann.target_audience == "admin" and user.role_name != "admin":
                continue

        # Check dismissal / show_count
        dismiss_result = await db.execute(
            select(PopupDismissal).where(
                PopupDismissal.announcement_id == ann.id,
                PopupDismissal.user_id == user.id,
            )
        )
        dismissal = dismiss_result.scalar_one_or_none()

        if dismissal:
            if ann.show_count > 0 and dismissal.seen_count >= ann.show_count:
                continue

        visible.append(_serialize(ann))

    return visible


@router.post("/{popup_id}/dismiss")
async def dismiss_popup(
    popup_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a popup as dismissed by the current user."""
    ann = await db.get(PopupAnnouncement, popup_id)
    if not ann:
        raise HTTPException(status_code=404, detail="הודעה לא נמצאה")

    # Check if already dismissed
    result = await db.execute(
        select(PopupDismissal).where(
            PopupDismissal.announcement_id == popup_id,
            PopupDismissal.user_id == user.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.seen_count += 1
        existing.dismissed_at = datetime.now(timezone.utc)
    else:
        db.add(PopupDismissal(
            announcement_id=popup_id,
            user_id=user.id,
            seen_count=1,
        ))

    await db.commit()
    return {"ok": True}
