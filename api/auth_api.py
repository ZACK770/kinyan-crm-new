"""
Auth API — login, register, Google OAuth, password reset.
Prefix: /api/auth
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, settings
from db.models import User
from api.dependencies import get_current_user
from services import audit_logs
from services.auth import (
    verify_password,
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
)
from services.users import (
    get_user_by_email,
    create_user,
    update_user_password,
    update_last_login,
    get_or_create_google_user,
)
from services.google_auth import (
    get_google_login_url,
    exchange_code_for_tokens,
    get_google_user_info,
    verify_google_id_token,
)
from services.email_service import send_password_reset_email, send_welcome_email
from api.dependencies import get_current_user

router = APIRouter()


# ── Schemas ──────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleCallbackRequest(BaseModel):
    code: str


class GoogleIdTokenRequest(BaseModel):
    id_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class MessageResponse(BaseModel):
    message: str


# ── Helpers ──────────────────────────────────────────
def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role_name": user.role_name,
        "permission_level": user.permission_level,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
    }


def _create_token_response(user: User) -> dict:
    token = create_access_token(
        user_id=user.id,
        email=user.email,
        permission_level=user.permission_level,
        role_name=user.role_name,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_to_dict(user),
    }


# ── Register ─────────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user. User starts as 'pending' (no permissions)
    until admin assigns a role. Gets redirected to welcome page.
    """
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="כתובת מייל זו כבר רשומה במערכת",
        )

    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="הסיסמה חייבת להכיל לפחות 6 תווים",
        )

    user = await create_user(
        db,
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        permission_level=0,
        role_name="pending",
    )

    # Send welcome email (non-blocking — don't fail registration if email fails)
    try:
        await send_welcome_email(user.email, user.full_name)
    except Exception:
        pass

    return _create_token_response(user)


# ── Login ────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Login with email + password."""
    user = await get_user_by_email(db, body.email)

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="מייל או סיסמה שגויים",
        )

    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="מייל או סיסמה שגויים",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="חשבון המשתמש אינו פעיל",
        )

    await update_last_login(db, user.id)
    
    # Log successful login
    await audit_logs.log_login(
        db=db,
        user=user,
        description=f"התחברות מוצלחת עם אימייל: {user.email}",
        request=request,
    )
    
    return _create_token_response(user)


# ── Google OAuth ─────────────────────────────────────
@router.get("/google/login-url")
async def google_login_url():
    """Get the Google OAuth consent URL. Frontend redirects the user here."""
    url = get_google_login_url()
    return {"url": url}


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(body: GoogleCallbackRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Exchange Google authorization code for tokens,
    get user info, and create/login the user.
    """
    try:
        tokens = await exchange_code_for_tokens(body.code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="שגיאה בהחלפת קוד Google",
        )

    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="לא התקבל טוקן מ-Google",
        )

    try:
        google_user = await get_google_user_info(access_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="שגיאה בקבלת פרטי משתמש מ-Google",
        )

    user = await get_or_create_google_user(
        db,
        google_id=str(google_user.get("id")),
        email=google_user.get("email", ""),
        full_name=google_user.get("name", ""),
        avatar_url=google_user.get("picture"),
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="חשבון המשתמש אינו פעיל",
        )

    # Log successful Google login
    await audit_logs.log_login(
        db=db,
        user=user,
        description=f"התחברות מוצלחת דרך Google: {user.email}",
        request=request,
    )

    return _create_token_response(user)


@router.post("/google/id-token", response_model=TokenResponse)
async def google_id_token_login(body: GoogleIdTokenRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Alternative: verify a Google ID token (from Google Sign-In button).
    Useful for frontend-only Google sign-in without server-side code exchange.
    """
    google_data = await verify_google_id_token(body.id_token)
    if not google_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="טוקן Google לא תקין",
        )

    user = await get_or_create_google_user(
        db,
        google_id=google_data.get("sub", ""),
        email=google_data.get("email", ""),
        full_name=google_data.get("name", ""),
        avatar_url=google_data.get("picture"),
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="חשבון המשתמש אינו פעיל",
        )

    # Log successful Google login
    await audit_logs.log_login(
        db=db,
        user=user,
        description=f"התחברות מוצלחת דרך Google ID Token: {user.email}",
        request=request,
    )

    return _create_token_response(user)


# ── Password Reset ───────────────────────────────────
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Request a password reset. Sends an email with a reset link.
    Always returns success to prevent email enumeration attacks.
    """
    user = await get_user_by_email(db, body.email)

    if user and user.is_active:
        token = create_password_reset_token(user.id, user.email)
        await send_password_reset_email(user.email, token)

    # Always return success (don't reveal whether email exists)
    return {"message": "אם הכתובת רשומה במערכת, נשלח אליה קישור לאיפוס סיסמה"}


@router.post("/reset-password", response_model=TokenResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using the token from the email link."""
    payload = decode_password_reset_token(body.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="קישור לא תקין או שפג תוקפו",
        )

    user_id = int(payload.get("sub", 0))
    user = await get_user_by_email(db, payload.get("email", ""))

    if not user or user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="קישור לא תקין",
        )

    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="הסיסמה חייבת להכיל לפחות 6 תווים",
        )

    await update_user_password(db, user.id, body.new_password)
    await update_last_login(db, user.id)

    # Return a fresh token so user is logged in
    # Refresh user from DB to get latest data
    from services.users import get_user_by_id
    user = await get_user_by_id(db, user.id)
    return _create_token_response(user)


# ── Change password (logged-in user) ────────────────
@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the currently logged-in user."""
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="החשבון שלך משתמש בהתחברות Google בלבד. הגדר סיסמה דרך 'שכחתי סיסמה'.",
        )

    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="סיסמה נוכחית שגויה",
        )

    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="הסיסמה חייבת להכיל לפחות 6 תווים",
        )

    await update_user_password(db, user.id, body.new_password)
    return {"message": "הסיסמה עודכנה בהצלחה"}


# ── Current user info ────────────────────────────────
@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get the current logged-in user's profile."""
    return _user_to_dict(user)
