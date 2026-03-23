"""Global table preferences API.

Provides admin-managed global SmartTable presets shared across all users.
Prefix: /api/table-prefs
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, require_permission
from db import get_db
from db.models import GlobalTablePref, User


router = APIRouter()


class GlobalTablePrefRequest(BaseModel):
    data: dict


@router.get("/global")
async def api_get_global_table_prefs(
    storage_key: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get global SmartTable preferences by storage_key."""
    result = await db.execute(
        select(GlobalTablePref).where(GlobalTablePref.storage_key == storage_key)
    )
    pref = result.scalar_one_or_none()
    return {"storage_key": storage_key, "data": pref.data if pref else None}


@router.put("/global")
async def api_set_global_table_prefs(
    body: GlobalTablePrefRequest,
    storage_key: str = Query(..., min_length=1),
    admin: User = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create or update global SmartTable preferences for all users."""
    result = await db.execute(
        select(GlobalTablePref).where(GlobalTablePref.storage_key == storage_key)
    )
    pref = result.scalar_one_or_none()

    if pref:
        pref.data = body.data
        pref.updated_by_user_id = admin.id if admin.id and admin.id > 0 else None
    else:
        pref = GlobalTablePref(
            storage_key=storage_key,
            data=body.data,
            updated_by_user_id=admin.id if admin.id and admin.id > 0 else None,
        )
        db.add(pref)

    await db.commit()
    await db.refresh(pref)
    return {"storage_key": storage_key, "data": pref.data}


@router.delete("/global")
async def api_delete_global_table_prefs(
    storage_key: str = Query(..., min_length=1),
    admin: User = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete global SmartTable preferences for a storage_key."""
    result = await db.execute(
        select(GlobalTablePref).where(GlobalTablePref.storage_key == storage_key)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        raise HTTPException(status_code=404, detail="לא נמצאה הגדרה גלובלית")

    await db.delete(pref)
    await db.commit()
    return {"ok": True}
