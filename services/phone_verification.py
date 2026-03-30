import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import settings
from db.models import PhoneVerificationChallenge
from services.yemot_api import run_tzintuk


DEFAULT_TTL_MINUTES = 5
MAX_ATTEMPTS = 5


def _hash_verify_code(code: str) -> bytes:
    secret = (settings.SECRET_KEY or "").encode("utf-8")
    return hashlib.sha256(secret + b":" + code.encode("utf-8")).digest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def start_phone_verification(db: AsyncSession, phone: str) -> str:
    """Sends tzintuk and stores challenge. Returns challenge_id."""
    resp = await run_tzintuk(phone, caller_id="RAND")
    verify_code = (resp or {}).get("verifyCode")
    if not verify_code:
        raise ValueError("Yemot did not return verifyCode (callerId must be RAND)")

    challenge_id = str(uuid4())
    expires_at = _now() + timedelta(minutes=DEFAULT_TTL_MINUTES)

    row = PhoneVerificationChallenge(
        id=challenge_id,
        phone=phone,
        verify_code_hash=_hash_verify_code(str(verify_code)),
        expires_at=expires_at,
        attempts=0,
        provider="yemot",
    )
    db.add(row)
    await db.flush()
    return challenge_id


async def verify_phone_challenge(db: AsyncSession, challenge_id: str, last4: str) -> str | None:
    """Verifies challenge and returns the verified phone, or None if invalid."""
    stmt = select(PhoneVerificationChallenge).where(PhoneVerificationChallenge.id == challenge_id)
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()
    if not row:
        return None

    if row.used_at is not None:
        return None

    if row.expires_at <= _now():
        return None

    if row.attempts >= MAX_ATTEMPTS:
        return None

    row.attempts += 1

    if row.verify_code_hash != _hash_verify_code(last4):
        await db.flush()
        return None

    row.used_at = _now()
    await db.flush()
    return row.phone
