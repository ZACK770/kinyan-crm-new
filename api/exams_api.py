"""
Exams API endpoints.
"""
from datetime import date
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
    exam_date: date | None = None
    questionnaire_url: str | None = None
    answers_url: str | None = None


class SubmissionCreate(BaseModel):
    student_id: int
    score: int | None = None
    status: str = "הוגש"
    student_notes: str | None = None
    internal_notes: str | None = None


class GradeSubmission(BaseModel):
    score: int
    status: str = "נבדק"
    internal_notes: str | None = None


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
