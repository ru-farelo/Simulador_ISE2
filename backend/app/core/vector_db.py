from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

vector_engine = create_engine(settings.vector_db_url)
VectorSessionLocal = sessionmaker(bind=vector_engine, autocommit=False, autoflush=False)


class VectorBase(DeclarativeBase):
    pass


def init_vector_db() -> None:
    """Create the pgvector extension and tables. Safe to call repeatedly."""
    with vector_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    from app.models import vector_models  # noqa: F401  (register models)

    VectorBase.metadata.create_all(bind=vector_engine)


def get_vector_db() -> Generator[Session, None, None]:
    db = VectorSessionLocal()
    try:
        yield db
    finally:
        db.close()
