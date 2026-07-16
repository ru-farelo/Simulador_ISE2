from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.planner import PlannerToday
from app.services import planner_service
from app.services.anthropic_client import AIServiceError

router = APIRouter(prefix="/api/planner", tags=["planner"])


@router.get("/today", response_model=PlannerToday)
def get_today(db: Session = Depends(get_db)) -> PlannerToday:
    try:
        return planner_service.get_today_plan(db)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
