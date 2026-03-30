"""
Exams API endpoints.
"""
from datetime import date as Date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import exams as exam_svc
from .dependencies import require_entity_access

router = APIRouter()


class ExamCreate(BaseModel):
    name: str
    course_id: int
    exam_type: str = "בכתב"
    lecturer_id: int | None = None
    exam_date: Optional[Date] = None
    questionnaire_url: str | None = None
    answers_url: str | None = None
    material: str | None = None
    registration_price: int | None = None
    registration_url: str | None = None
    is_registration_open: bool | None = None


class ExamUpdate(BaseModel):
    name: str | None = None
    course_id: int | None = None
    exam_type: str | None = None
    lecturer_id: int | None = None
    exam_date: Optional[Date] = None
    questionnaire_url: str | None = None
    answers_url: str | None = None
    material: str | None = None
    registration_price: int | None = None
    registration_url: str | None = None
    is_registration_open: bool | None = None


class SubmissionCreate(BaseModel):
    student_id: int
    score: int | None = None
    status: str = "הוגש"
    student_notes: str | None = None
    internal_notes: str | None = None


@router.get("/")
async def list_exams(
    course_id: int | None = Query(None),
    limit: int = Query(200, le=1000),
    user=Depends(require_entity_access("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List exams, optionally filtered by course_id."""
    items = await exam_svc.list_exams(db, limit=limit, course_id=course_id)

    return [
        {
            "id": e.id,
            "name": e.name,
            "exam_type": e.exam_type,
            "exam_date": str(e.exam_date) if e.exam_date else None,
            "course_id": e.course_id,
            "lecturer_id": e.lecturer_id,
            "questionnaire_url": e.questionnaire_url,
            "answers_url": e.answers_url,
            "material": e.material,
            "registration_price": e.registration_price,
            "registration_url": e.registration_url,
            "is_registration_open": e.is_registration_open,
        }
        for e in items
    ]


class GradeSubmission(BaseModel):
    score: int
    status: str = "נבדק"
    internal_notes: str | None = None


class ExamDateCreate(BaseModel):
    date: Date
    description: str | None = None
    is_active: bool = True
    max_registrations: int | None = None


class ExamDateUpdate(BaseModel):
    date: Optional[Date] = None
    description: str | None = None
    is_active: bool | None = None
    max_registrations: int | None = None


class ExamDateAssignRequest(BaseModel):
    exam_id: int


@router.get("/course/{course_id}")
async def list_course_exams(
    course_id: int,
    user = Depends(require_entity_access("exams", "view")),
    db: AsyncSession = Depends(get_db)
):
    items = await exam_svc.list_course_exams(db, course_id)
    return [
        {
            "id": e.id,
            "name": e.name,
            "exam_type": e.exam_type,
            "exam_date": str(e.exam_date) if e.exam_date else None,
        }
        for e in items
    ]


@router.get("/exam-dates")
async def list_exam_dates(
    limit: int = Query(500, le=2000),
    user = Depends(require_entity_access("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await exam_svc.list_exam_dates(db, limit=limit)
    return [
        {
            "id": x.id,
            "date": str(x.date),
            "description": x.description,
            "is_active": x.is_active,
            "max_registrations": x.max_registrations,
            "created_at": str(x.created_at),
        }
        for x in items
    ]


@router.post("/exam-dates")
async def create_exam_date(
    data: ExamDateCreate,
    user = Depends(require_entity_access("exams", "create")),
    db: AsyncSession = Depends(get_db),
):
    ed = await exam_svc.create_exam_date(
        db,
        date_value=data.date,
        description=data.description,
        is_active=data.is_active,
        max_registrations=data.max_registrations,
    )
    await db.commit()
    return {"id": ed.id}


@router.patch("/exam-dates/{exam_date_id}")
async def update_exam_date(
    exam_date_id: int,
    data: ExamDateUpdate,
    user = Depends(require_entity_access("exams", "edit")),
    db: AsyncSession = Depends(get_db),
):
    ed = await exam_svc.update_exam_date(
        db,
        exam_date_id,
        date_value=data.date,
        description=data.description,
        is_active=data.is_active,
        max_registrations=data.max_registrations,
    )
    if not ed:
        raise HTTPException(404, "ExamDate not found")
    await db.commit()
    return {"id": ed.id}


@router.delete("/exam-dates/{exam_date_id}")
async def delete_exam_date(
    exam_date_id: int,
    user = Depends(require_entity_access("exams", "delete")),
    db: AsyncSession = Depends(get_db),
):
    ok = await exam_svc.delete_exam_date(db, exam_date_id)
    if not ok:
        raise HTTPException(404, "ExamDate not found")
    await db.commit()
    return {"ok": True}


@router.get("/exam-dates/{exam_date_id}/exams")
async def list_exams_for_exam_date(
    exam_date_id: int,
    user = Depends(require_entity_access("exams", "view")),
    db: AsyncSession = Depends(get_db),
):
    items = await exam_svc.list_exam_date_exams(db, exam_date_id)
    return [
        {
            "id": e.id,
            "name": e.name,
            "exam_type": e.exam_type,
            "course_id": e.course_id,
            "registration_price": e.registration_price,
            "registration_url": e.registration_url,
            "is_registration_open": e.is_registration_open,
        }
        for e in items
    ]


@router.post("/exam-dates/{exam_date_id}/exams")
async def assign_exam_to_exam_date(
    exam_date_id: int,
    data: ExamDateAssignRequest,
    user = Depends(require_entity_access("exams", "edit")),
    db: AsyncSession = Depends(get_db),
):
    await exam_svc.assign_exam_to_date(db, exam_date_id, data.exam_id)
    await db.commit()
    return {"ok": True}


@router.delete("/exam-dates/{exam_date_id}/exams/{exam_id}")
async def unassign_exam_from_exam_date(
    exam_date_id: int,
    exam_id: int,
    user = Depends(require_entity_access("exams", "edit")),
    db: AsyncSession = Depends(get_db),
):
    await exam_svc.unassign_exam_from_date(db, exam_date_id, exam_id)
    await db.commit()
    return {"ok": True}


@router.post("/")
async def create_exam(
    data: ExamCreate,
    user = Depends(require_entity_access("exams", "create")),
    db: AsyncSession = Depends(get_db)
):
    exam = await exam_svc.create_exam(db, **data.model_dump())
    await db.commit()
    return {"id": exam.id, "name": exam.name}


@router.get("/{exam_id}")
async def get_exam(
    exam_id: int,
    user = Depends(require_entity_access("exams", "view")),
    db: AsyncSession = Depends(get_db)
):
    exam = await exam_svc.get_exam_with_submissions(db, exam_id)
    if not exam:
        raise HTTPException(404, "Exam not found")
    avg = await exam_svc.get_exam_average(db, exam_id)
    return {
        "id": exam.id,
        "name": exam.name,
        "exam_type": exam.exam_type,
        "exam_date": str(exam.exam_date) if exam.exam_date else None,
        "course_id": exam.course_id,
        "lecturer_id": exam.lecturer_id,
        "questionnaire_url": exam.questionnaire_url,
        "answers_url": exam.answers_url,
        "material": exam.material,
        "registration_price": exam.registration_price,
        "registration_url": exam.registration_url,
        "is_registration_open": exam.is_registration_open,
        "average_score": avg,
        "submissions": [
            {
                "id": s.id,
                "student_id": s.student_id,
                "score": s.score,
                "status": s.status,
                "submitted_at": str(s.submitted_at) if s.submitted_at else None,
            }
            for s in exam.submissions
        ],
    }


@router.patch("/{exam_id}")
async def update_exam(
    exam_id: int,
    data: ExamUpdate,
    user = Depends(require_entity_access("exams", "edit")),
    db: AsyncSession = Depends(get_db),
):
    exam = await exam_svc.update_exam(db, exam_id, **data.model_dump(exclude_unset=True))
    if not exam:
        raise HTTPException(404, "Exam not found")
    await db.commit()
    return {"id": exam.id}


@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: int,
    user = Depends(require_entity_access("exams", "delete")),
    db: AsyncSession = Depends(get_db),
):
    try:
        ok = await exam_svc.delete_exam(db, exam_id)
        if not ok:
            raise HTTPException(404, "Exam not found")
        await db.commit()
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{exam_id}/submissions")
async def add_submission(
    exam_id: int,
    data: SubmissionCreate,
    user = Depends(require_entity_access("exams", "edit")),
    db: AsyncSession = Depends(get_db)
):
    submission = await exam_svc.add_submission(db, exam_id, **data.model_dump())
    await db.commit()
    return {"id": submission.id, "status": submission.status}


@router.patch("/submissions/{submission_id}/grade")
async def grade_submission(
    submission_id: int,
    data: GradeSubmission,
    user = Depends(require_entity_access("exams", "edit")),
    db: AsyncSession = Depends(get_db)
):
    sub = await exam_svc.grade_submission(db, submission_id, **data.model_dump())
    if not sub:
        raise HTTPException(404, "Submission not found")
    await db.commit()
    return {"id": sub.id, "score": sub.score, "status": sub.status}
