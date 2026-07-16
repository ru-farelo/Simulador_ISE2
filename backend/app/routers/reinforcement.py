from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.reinforcement import DueReinforcementItem, ReinforcementReviewRequest, ReinforcementReviewResult
from app.services import reinforcement_service
from app.services.anthropic_client import AIServiceError

router = APIRouter(prefix="/api/reinforcement", tags=["reinforcement"])


@router.get("/due", response_model=list[DueReinforcementItem])
def get_due(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)) -> list[DueReinforcementItem]:
    try:
        return reinforcement_service.get_due_reinforcement(db, limit)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{item_id}/review", response_model=ReinforcementReviewResult)
def review(
    item_id: int,
    request: ReinforcementReviewRequest,
    db: Session = Depends(get_db),
) -> ReinforcementReviewResult:
    try:
        return reinforcement_service.review_reinforcement(db, item_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
