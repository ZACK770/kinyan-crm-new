from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List

from db import get_db
from services.exam_registration import (
    get_upcoming_exam_dates,
    create_exam_registration,
    get_examinee_registrations
)

router = APIRouter()


# Pydantic models
class ExamRegistrationRequest(BaseModel):
    exam_date_id: int = Field(..., description="ID of the exam date")
    exam_id: int = Field(..., description="ID of the exam")
    phone: str = Field(..., description="Examinee phone number")
    name: Optional[str] = Field(None, description="Examinee name (auto-created if not exists)")
    notes: Optional[str] = Field(None, description="Registration notes")


class ExamRegistrationResponse(BaseModel):
    registration_id: int
    registration_code: str
    exam_date: str
    exam_name: str
    examinee_name: str
    examinee_phone: str
    status: str
    created_at: str


class ExamDateInfo(BaseModel):
    exam_date_id: int
    date: str
    description: Optional[str]
    max_registrations: Optional[int]
    exams: List[dict]


class RegistrationInfo(BaseModel):
    registration_id: int
    registration_code: str
    exam_date: str
    exam_name: str
    exam_type: str
    course_name: Optional[str]
    status: str
    notes: Optional[str]
    created_at: str


@router.get("/exam-dates/upcoming", response_model=List[ExamDateInfo])
async def get_upcoming_exams(
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming exam dates with available exams for registration."""
    try:
        exam_dates = await get_upcoming_exam_dates(db)
        return exam_dates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", response_model=ExamRegistrationResponse)
async def register_for_exam(
    request: ExamRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register an examinee for an exam."""
    try:
        registration = await create_exam_registration(
            db=db,
            exam_date_id=request.exam_date_id,
            exam_id=request.exam_id,
            phone=request.phone,
            name=request.name,
            notes=request.notes
        )
        return registration
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registrations/{phone}", response_model=List[RegistrationInfo])
async def get_registrations_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all registrations for an examinee by phone number."""
    try:
        registrations = await get_examinee_registrations(db, phone)
        return registrations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
