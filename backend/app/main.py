from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.db import init_db
from app.core.vector_db import init_vector_db
from app.routers import dashboard, learning, listening, planner, rag, reading, reinforcement, speaking, writing

settings = get_settings()

app = FastAPI(title="Trinity ISE II Coach API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    try:
        init_vector_db()
    except Exception as exc:  # noqa: BLE001 — RAG is optional, never block the API on it
        print(f"[startup] Vector DB unavailable, RAG will be disabled: {exc}")


app.include_router(dashboard.router)
app.include_router(reading.router)
app.include_router(writing.router)
app.include_router(speaking.router)
app.include_router(listening.router)
app.include_router(rag.router)
app.include_router(learning.router)
app.include_router(reinforcement.router)
app.include_router(planner.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
