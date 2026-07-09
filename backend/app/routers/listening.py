from fastapi import APIRouter, HTTPException, Query

from app.models.speaking import ListeningPassage
from app.services import listening_service
from app.services.anthropic_client import AIServiceError

router = APIRouter(prefix="/api/listening", tags=["listening"])


@router.get("/passage", response_model=ListeningPassage)
def get_passage(
    mode: str = Query("fixed", pattern="^(fixed|generated)$"),
    passage_id: str | None = None,
) -> ListeningPassage:
    if mode == "generated":
        try:
            return listening_service.generate_passage()
        except AIServiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    try:
        return listening_service.get_fixed_passage(passage_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
