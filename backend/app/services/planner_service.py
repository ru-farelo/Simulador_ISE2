"""Combines Block 1 (learning) due counts, Block 2 (reinforcement) due
count, and the dashboard's top error categories into one daily proposal.
Deterministic on purpose — the personalisation already happened when each
item/drill was generated from the candidate's own material; this layer
only needs to sequence what's already there, so it doesn't spend an extra
Claude call just to decide what order to show things in.
"""

import datetime as dt

from sqlalchemy.orm import Session

from app.models.planner import PlannerBlock, PlannerToday
from app.services import dashboard_service, learning_service, reinforcement_service

BLOCK_LABELS: dict[str, str] = {
    "vocab": "Vocabulario",
    "grammar": "Gramática",
    "filler": "Fillers",
    "connector": "Conectores",
    "pronunciation": "Pronunciación",
}


def _build_suggestion(blocks: list[PlannerBlock], reinforcement_count: int, top_errors: list) -> str:
    if reinforcement_count > 0:
        parts = [
            f"Tienes {reinforcement_count} error{'es' if reinforcement_count != 1 else ''} recurrente"
            f"{'s' if reinforcement_count != 1 else ''} pendiente{'s' if reinforcement_count != 1 else ''} de "
            "repasar — empieza por el Bloque 2 (Refuerzo)."
        ]
    else:
        parts = ["No tienes errores pendientes de refuerzo hoy."]

    learning_blocks = [b for b in blocks if b.type != "reinforcement" and b.due_count > 0]
    if learning_blocks:
        top_block = max(learning_blocks, key=lambda b: b.due_count)
        parts.append(f"Después, {top_block.label} tiene {top_block.due_count} ítem(s) esperando.")
    elif reinforcement_count == 0:
        parts.append("Tampoco hay ítems de Aprendizaje pendientes ahora mismo — vuelve más tarde.")

    if top_errors:
        parts.append(f"Tu error más frecuente últimamente es «{top_errors[0].category}» — presta atención extra.")

    return " ".join(parts)


def get_today_plan(db: Session) -> PlannerToday:
    blocks = [
        PlannerBlock(type=item_type, label=label, due_count=learning_service.count_due_items(db, item_type))
        for item_type, label in BLOCK_LABELS.items()
    ]
    reinforcement_count = reinforcement_service.count_due_reinforcement(db)
    blocks.append(PlannerBlock(type="reinforcement", label="Refuerzo de errores", due_count=reinforcement_count))

    summary = dashboard_service.get_summary(db)

    return PlannerToday(
        date=dt.datetime.now(dt.timezone.utc).date(),
        blocks=blocks,
        total_due=sum(b.due_count for b in blocks),
        top_error_categories=summary.top_error_categories,
        suggestion=_build_suggestion(blocks, reinforcement_count, summary.top_error_categories),
    )
