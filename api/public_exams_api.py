from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services.phone_verification import start_phone_verification, verify_phone_challenge
from services.public_exams import get_exam_results_by_phone

router = APIRouter()


class StartAuthRequest(BaseModel):
    phone: str


class StartAuthResponse(BaseModel):
    challenge_id: str


class VerifyAuthRequest(BaseModel):
    challenge_id: str
    last4: str


@router.post("/auth/start", response_model=StartAuthResponse)
async def start_auth(data: StartAuthRequest, db: AsyncSession = Depends(get_db)):
    try:
        challenge_id = await start_phone_verification(db, data.phone)
        await db.commit()
        return {"challenge_id": challenge_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/verify")
async def verify_auth(data: VerifyAuthRequest, db: AsyncSession = Depends(get_db)):
    phone = await verify_phone_challenge(db, data.challenge_id, data.last4)
    if not phone:
        await db.rollback()
        raise HTTPException(status_code=401, detail="Invalid verification")

    results = await get_exam_results_by_phone(db, phone)
    await db.commit()

    if not results:
        return {"message": "לא נמצאו מבחנים", "exams": []}

    return {"exams": results}
