"""
User management API — admin panel for managing users & permissions.
Prefix: /api/users
Requires manager/admin role for most operations.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import User
from api.dependencies import get_current_user, require_permission
from services.users import (
    list_users,
    count_users,
    get_user_by_id,
    update_user_role,
    update_user_profile,
    deactivate_user,
    delete_user,
    create_user,
    get_all_entity_permissions,
    set_entity_permission,
    ROLES,
)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role_name: str
    permission_level: int
    avatar_url: Optional[str] = None
    is_active: bool
    last_login: Optional[str] = None
    created_at: Optional[str] = None


class UpdateRoleRequest(BaseModel):
    role_name: str  # pending / viewer / editor / manager / admin


class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role_name: str = "viewer"


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


class SetEntityPermissionRequest(BaseModel):
    entity_name: str
    action: str  # view / create / edit / delete
    required_level: int


# ── Helpers ──────────────────────────────────────────
def _user_to_response(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role_name": user.role_name,
        "permission_level": user.permission_level,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        "last_login": str(user.last_login) if user.last_login else None,
        "created_at": str(user.created_at) if user.created_at else None,
    }


# ── List users ───────────────────────────────────────
@router.get("/")
async def api_list_users(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    role: Optional[str] = Query(None),
    admin: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """List all users. Requires manager+ role."""
    users = await list_users(db, limit=limit, offset=offset, role=role)
    total = await count_users(db)
    return {
        "items": [_user_to_response(u) for u in users],
        "total": total,
    }


# ── Get single user ─────────────────────────────────
@router.get("/{user_id}")
async def api_get_user(
    user_id: int,
    admin: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user by ID. Requires manager+ role."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")
    return _user_to_response(user)


# ── Create user (admin) ─────────────────────────────
@router.post("/")
async def api_create_user(
    body: CreateUserRequest,
    admin: User = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user with a specific role. Requires admin role."""
    from services.users import get_user_by_email, role_to_level

    if body.role_name not in ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"תפקיד לא חוקי. האפשרויות: {', '.join(ROLES.keys())}",
        )

    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=409, detail="כתובת מייל כבר רשומה")

    user = await create_user(
        db,
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        permission_level=role_to_level(body.role_name),
        role_name=body.role_name,
    )

    # Auto-create salesperson record if role is salesperson
    from services.sales import ensure_salesperson_for_user
    await ensure_salesperson_for_user(db, user)

    return _user_to_response(user)


# ── Update user (general PATCH) ─────────────────────
class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


@router.patch("/{user_id}")
async def api_update_user(
    user_id: int,
    body: UpdateUserRequest,
    admin: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's details. Requires manager+ role."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    # Update role if provided (admin only)
    if body.role_name is not None:
        if body.role_name not in ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"תפקיד לא חוקי. האפשרויות: {', '.join(ROLES.keys())}",
            )
        if admin.permission_level < 40:
            raise HTTPException(status_code=403, detail="רק מנהל מערכת יכול לשנות תפקידים")
        user = await update_user_role(db, user_id, body.role_name)

    # Update profile fields
    if body.full_name is not None or body.email is not None:
        user = await update_user_profile(db, user_id, full_name=body.full_name, email=body.email)

    # Update active status
    if body.is_active is not None and not body.is_active:
        await deactivate_user(db, user_id)
        user = await get_user_by_id(db, user_id)
    elif body.is_active is not None and body.is_active and not user.is_active:
        user.is_active = True
        await db.commit()
        await db.refresh(user)

    # Update password
    if body.password:
        from services.auth import hash_password
        user.hashed_password = hash_password(body.password)
        await db.commit()
        await db.refresh(user)

    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    # Sync salesperson record when role changes
    from services.sales import ensure_salesperson_for_user
    await ensure_salesperson_for_user(db, user)

    return _user_to_response(user)


# ── Update user role ─────────────────────────────────
@router.put("/{user_id}/role")
async def api_update_role(
    user_id: int,
    body: UpdateRoleRequest,
    admin: User = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role/permission level. Requires admin role."""
    if body.role_name not in ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"תפקיד לא חוקי. האפשרויות: {', '.join(ROLES.keys())}",
        )

    # Cannot demote yourself
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="לא ניתן לשנות את התפקיד של עצמך")

    user = await update_user_role(db, user_id, body.role_name)
    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    # Sync salesperson record when role changes
    from services.sales import ensure_salesperson_for_user
    await ensure_salesperson_for_user(db, user)

    return _user_to_response(user)


# ── Update user profile ─────────────────────────────
@router.put("/{user_id}/profile")
async def api_update_profile(
    user_id: int,
    body: UpdateProfileRequest,
    admin: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's profile. Requires manager+ role."""
    user = await update_user_profile(
        db, user_id, full_name=body.full_name, email=body.email,
    )
    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")
    return _user_to_response(user)


# ── Deactivate user ──────────────────────────────────
@router.put("/{user_id}/deactivate")
async def api_deactivate_user(
    user_id: int,
    admin: User = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user account. Requires admin role."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="לא ניתן להשבית את החשבון שלך")

    success = await deactivate_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")
    return {"message": "המשתמש הושבת בהצלחה"}


# ── Delete user ──────────────────────────────────────
@router.delete("/{user_id}")
async def api_delete_user(
    user_id: int,
    admin: User = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user permanently. Requires admin role."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="לא ניתן למחוק את החשבון שלך")

    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")
    return {"message": "המשתמש נמחק בהצלחה"}


# ── Entity Permissions management ────────────────────
@router.get("/permissions/entities")
async def api_get_entity_permissions(
    admin: User = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get all entity permission settings. Requires admin role."""
    perms = await get_all_entity_permissions(db)
    return {"permissions": perms, "roles": ROLES}


@router.put("/permissions/entities")
async def api_set_entity_permission(
    body: SetEntityPermissionRequest,
    admin: User = Depends(require_permission("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Set the required permission level for an entity+action. Requires admin role."""
    valid_actions = {"view", "create", "edit", "delete"}
    if body.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"פעולה לא חוקית. האפשרויות: {', '.join(valid_actions)}",
        )
    if body.required_level not in ROLES.values():
        raise HTTPException(
            status_code=400,
            detail=f"רמת הרשאה לא חוקית. האפשרויות: {list(ROLES.values())}",
        )

    perm = await set_entity_permission(db, body.entity_name, body.action, body.required_level)
    return {
        "entity_name": perm.entity_name,
        "action": perm.action,
        "required_level": perm.required_level,
    }


# ── Available roles reference ────────────────────────
@router.get("/roles/list")
async def api_list_roles(admin: User = Depends(require_permission("manager"))):
    """Get list of available roles with their levels."""
    return {
        "roles": [
            {"name": name, "level": level, "label_he": _role_label_he(name)}
            for name, level in ROLES.items()
        ]
    }


def _role_label_he(role: str) -> str:
    labels = {
        "pending": "ממתין לאישור",
        "viewer": "צופה",
        "editor": "עורך",
        "manager": "מנהל",
        "admin": "מנהל מערכת",
    }
    return labels.get(role, role)
