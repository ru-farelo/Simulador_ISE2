from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.reading_exam import ReadingExamPublic, ReadingExamResult, ReadingExamSubmission
from app.services import reading_service
from app.services.anthropic_client import AIServiceError

router = APIRouter(prefix="/api/reading", tags=["reading"])


@router.get("/exam", response_model=ReadingExamPublic)
def get_exam(
    mode: str = Query("fixed", pattern="^(fixed|generated)$"),
    exam_id: str | None = None,
    db: Session = Depends(get_db),
) -> ReadingExamPublic:
    if mode == "generated":
        try:
            return reading_service.generate_exam(db)
        except AIServiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    try:
        return reading_service.get_fixed_exam(exam_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/submit", response_model=ReadingExamResult)
def submit_exam(
    submission: ReadingExamSubmission,
    db: Session = Depends(get_db),
) -> ReadingExamResult:
    try:
        return reading_service.grade_submission(db, submission)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
