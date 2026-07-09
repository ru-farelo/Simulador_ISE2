from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.schemas import DashboardSummary
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    return dashboard_service.get_summary(db)
