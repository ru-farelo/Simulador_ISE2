from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.learning import DueItem, LearningItemType, LearningReviewRequest, LearningReviewResult
from app.services import learning_service
from app.services.anthropic_client import AIServiceError

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.get("/due", response_model=list[DueItem])
def get_due(
    type: LearningItemType = Query(...),
    limit: int = Query(5, ge=1, le=20),
    category: str | None = Query(None, pattern="^(general|thematic)$"),
    db: Session = Depends(get_db),
) -> list[DueItem]:
    try:
        return learning_service.get_due_items(db, type, limit, category)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{item_id}/review", response_model=LearningReviewResult)
def review(
    item_id: int,
    request: LearningReviewRequest,
    db: Session = Depends(get_db),
) -> LearningReviewResult:
    try:
        return learning_service.review_item(db, item_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
