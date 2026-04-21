"""
User management service — CRUD + permission logic.
Available system-wide via: from services.users import ...
"""
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, EntityPermission
from services.auth import hash_password

# ── Role definitions ─────────────────────────────────
ROLES = {
    "pending": 0,
    "viewer": 10,
    "editor": 20,
    "salesperson": 25,  # אנשי מכירות - גישה מלאה ללידים, לא יכולים לנהל משתמשים
    "manager": 30,
    "admin": 40,
}

ROLE_NAMES = {v: k for k, v in ROLES.items()}


def role_to_level(role_name: str) -> int:
    """Convert role name to numeric level."""
    return ROLES.get(role_name, 0)


def level_to_role(level: int) -> str:
    """Convert numeric level to role name."""
    return ROLE_NAMES.get(level, "pending")


# ── Default entity permissions ───────────────────────
# Used when no DB record exists for an entity/action pair
DEFAULT_ENTITY_PERMISSIONS = {
    # entity_name: { action: required_level }
    "leads":       {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול ליצור ולערוך
    "students":    {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול ליצור ולערוך
    "courses":     {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול לצפות ולערוך
    "campaigns":   {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול לצפות ולערוך
    "salespeople": {"view": 10, "create": 30, "edit": 30, "delete": 40},
    "payments":    {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול ליצור ולערוך
    "expenses":    {"view": 20, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול לצפות ולערוך
    "exams":       {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול ליצור ולערוך
    "inquiries":   {"view": 10, "create": 10, "edit": 20, "delete": 30},  # salesperson (25) יכול ליצור ולערוך
    "collections": {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול ליצור ולערוך
    "commitments": {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול ליצור ולערוך
    "tasks":       {"view": 10, "create": 20, "edit": 20, "delete": 30},  # salesperson (25) יכול ליצור ולערוך
    "users":       {"view": 30, "create": 40, "edit": 40, "delete": 40},  # salesperson (25) לא יכול לנהל משתמשים
    "dashboard":   {"view": 10, "create": 40, "edit": 40, "delete": 40},
}


# ── User CRUD ────────────────────────────────────────
async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    role: Optional[str] = None,
) -> List[User]:
    stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    if role:
        stmt = stmt.where(User.role_name == role)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_users(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(User.id)))
    return result.scalar_one()


async def create_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    password: Optional[str] = None,
    google_id: Optional[str] = None,
    avatar_url: Optional[str] = None,
    permission_level: int = 0,
    role_name: str = "pending",
) -> User:
    """Create a new user. Password is hashed automatically."""
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password) if password else None,
        google_id=google_id,
        avatar_url=avatar_url,
        permission_level=permission_level,
        role_name=role_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_role(
    db: AsyncSession if True else None,
    user_id: int,
    role_name: str,
) -> Optional[User]:
    """Update a user's role/permission level."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.role_name = role_name
    user.permission_level = role_to_level(role_name)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_password(db: AsyncSession, user_id: int, new_password: str) -> bool:
    """Update user's password (hash it)."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    user.hashed_password = hash_password(new_password)
    await db.commit()
    return True


async def update_user_profile(
    db: AsyncSession,
    user_id: int,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> Optional[User]:
    """Update basic profile fields."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    if full_name is not None:
        user.full_name = full_name
    if email is not None:
        user.email = email
    if avatar_url is not None:
        user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(user)
    return user


async def update_last_login(db: AsyncSession, user_id: int):
    """Record last login timestamp."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.now(timezone.utc)
        await db.commit()


async def deactivate_user(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    user.is_active = False
    await db.commit()
    return True


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True


# ── Google auth helpers ──────────────────────────────
async def get_or_create_google_user(
    db: AsyncSession,
    google_id: str,
    email: str,
    full_name: str,
    avatar_url: Optional[str] = None,
) -> User:
    """Find user by google_id or email, or create a new pending user."""
    # Try google_id first
    user = await get_user_by_google_id(db, google_id)
    if user:
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        if avatar_url:
            user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
        return user

    # Try email (user might have registered with password first)
    user = await get_user_by_email(db, email)
    if user:
        # Link google account
        user.google_id = google_id
        user.last_login = datetime.now(timezone.utc)
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
        return user

    # Create new pending user
    return await create_user(
        db,
        email=email,
        full_name=full_name,
        google_id=google_id,
        avatar_url=avatar_url,
        permission_level=0,
        role_name="pending",
    )


# ── Entity permission checks ────────────────────────
async def get_required_level(
    db: AsyncSession,
    entity_name: str,
    action: str,
) -> int:
    """Get the required permission level for an entity/action.
    Checks DB first, falls back to DEFAULT_ENTITY_PERMISSIONS.
    """
    result = await db.execute(
        select(EntityPermission).where(
            EntityPermission.entity_name == entity_name,
            EntityPermission.action == action,
        )
    )
    perm = result.scalar_one_or_none()
    if perm:
        return perm.required_level

    # Fallback to defaults
    defaults = DEFAULT_ENTITY_PERMISSIONS.get(entity_name, {})
    return defaults.get(action, 10)  # default: viewer can view


def check_permission(user_level: int, required_level: int) -> bool:
    """Check if user's permission level meets the requirement."""
    return user_level >= required_level


async def set_entity_permission(
    db: AsyncSession,
    entity_name: str,
    action: str,
    required_level: int,
) -> EntityPermission:
    """Set or update the required permission level for an entity/action."""
    result = await db.execute(
        select(EntityPermission).where(
            EntityPermission.entity_name == entity_name,
            EntityPermission.action == action,
        )
    )
    perm = result.scalar_one_or_none()
    if perm:
        perm.required_level = required_level
    else:
        perm = EntityPermission(
            entity_name=entity_name,
            action=action,
            required_level=required_level,
        )
        db.add(perm)
    await db.commit()
    await db.refresh(perm)
    return perm


async def get_all_entity_permissions(db: AsyncSession) -> dict:
    """Get all entity permissions (DB overrides + defaults merged)."""
    result = await db.execute(select(EntityPermission))
    db_perms = result.scalars().all()

    # Start with defaults
    merged = {}
    for entity, actions in DEFAULT_ENTITY_PERMISSIONS.items():
        merged[entity] = dict(actions)

    # Override with DB values
    for perm in db_perms:
        if perm.entity_name not in merged:
            merged[perm.entity_name] = {}
        merged[perm.entity_name][perm.action] = perm.required_level

    return merged
