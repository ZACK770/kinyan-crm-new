"""
Auth dependencies for FastAPI routes.
Provides get_current_user and permission-checking helpers.
Import these in any API module that needs authentication.

Usage:
    from api.dependencies import get_current_user, require_permission

    @router.get("/")
    async def my_endpoint(user: User = Depends(get_current_user)):
        ...

    @router.get("/admin-only")
    async def admin_only(user: User = Depends(require_permission("admin"))):
        ...

    # Entity-level permissions:
    @router.get("/leads")
    async def list_leads(
        user: User = Depends(require_entity_access("leads", "view")),
        db: AsyncSession = Depends(get_db),
    ):
        ...
"""
from typing import Optional, Callable

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import User
from services.auth import decode_access_token
from services.users import get_user_by_id, ROLES, get_required_level, check_permission

# Bearer token scheme — reads "Authorization: Bearer <token>" header
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT token from the Authorization header.
    Returns the full User object from the database.
    Raises 401 if token is missing/invalid/expired or user not found.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="לא נשלח טוקן הזדהות",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="טוקן לא תקין או שפג תוקפו",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub", 0))
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="משתמש לא נמצא",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="חשבון המשתמש אינו פעיל",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Same as get_current_user but returns None instead of raising 401."""
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    user_id = int(payload.get("sub", 0))
    return await get_user_by_id(db, user_id)


def require_permission(min_role: str) -> Callable:
    """
    Dependency factory: ensures the current user has at least the given role.
    Usage: user = Depends(require_permission("manager"))

    Roles hierarchy: pending(0) < viewer(10) < editor(20) < manager(30) < admin(40)
    """
    required_level = ROLES.get(min_role, 0)

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.permission_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"נדרשת הרשאת {min_role} לפחות. ההרשאה שלך: {user.role_name}",
            )
        return user

    return _check


def require_entity_access(entity_name: str, action: str) -> Callable:
    """
    Dependency factory: checks if the user has permission for a specific entity+action.
    Reads the required level from DB (or defaults), then compares to user's level.
    """
    async def _check(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        required = await get_required_level(db, entity_name, action)
        if not check_permission(user.permission_level, required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"אין לך הרשאה ל-{action} ב-{entity_name}. נדרש רמה {required}, יש לך {user.permission_level}",
            )
        return user

    return _check


def require_active_user() -> Callable:
    """Ensures the user has at least 'pending' status but is active (not deactivated).
    For the 'welcome' page — even pending users should be able to see it."""
    async def _check(user: User = Depends(get_current_user)) -> User:
        # get_current_user already checks is_active
        return user

    return _check
