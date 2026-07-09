from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.speaking import (
    SpeakingCorrectionRequest,
    SpeakingCorrectionResult,
    SpeakingTaskName,
    SpeakingTurnRequest,
    SpeakingTurnResponse,
)
from app.services import speaking_service
from app.services.anthropic_client import AIServiceError

router = APIRouter(prefix="/api/speaking", tags=["speaking"])


@router.get("/conversation/topic")
def get_conversation_topic() -> dict[str, str]:
    return {"topic": speaking_service.pick_conversation_topic()}


@router.post("/{task_name}/turn", response_model=SpeakingTurnResponse)
def post_turn(
    request: SpeakingTurnRequest,
    task_name: SpeakingTaskName = Path(...),
) -> SpeakingTurnResponse:
    try:
        return speaking_service.get_examiner_turn(task_name, request.history, request.context)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/correct", response_model=SpeakingCorrectionResult)
def correct_session(
    request: SpeakingCorrectionRequest,
    db: Session = Depends(get_db),
) -> SpeakingCorrectionResult:
    try:
        return speaking_service.correct_session(db, request)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
