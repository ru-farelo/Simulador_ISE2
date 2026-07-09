import datetime as dt

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.db_models import RagRetrievalLog

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RagLogEntry(BaseModel):
    id: int
    query_text: str
    used_in: str
    results: list[dict]
    created_at: dt.datetime


@router.get("/logs", response_model=list[RagLogEntry])
def get_logs(limit: int = 20, db: Session = Depends(get_db)) -> list[RagLogEntry]:
    rows = db.execute(
        select(RagRetrievalLog).order_by(RagRetrievalLog.created_at.desc()).limit(limit)
    ).scalars().all()
    return [RagLogEntry.model_validate(row, from_attributes=True) for row in rows]
