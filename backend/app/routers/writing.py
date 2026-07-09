from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.writing import WritingCorrectionResult, WritingPrompt, WritingSubmission
from app.services import writing_service
from app.services.anthropic_client import AIServiceError

router = APIRouter(prefix="/api/writing", tags=["writing"])


@router.get("/prompt", response_model=WritingPrompt)
def get_prompt(
    mode: str = Query("fixed", pattern="^(fixed|generated)$"),
    prompt_id: str | None = None,
) -> WritingPrompt:
    if mode == "generated":
        try:
            return writing_service.generate_prompt()
        except AIServiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    try:
        return writing_service.get_fixed_prompt(prompt_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/submit", response_model=WritingCorrectionResult)
def submit_writing(
    submission: WritingSubmission,
    db: Session = Depends(get_db),
) -> WritingCorrectionResult:
    try:
        return writing_service.correct_submission(db, submission)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
