import logging
from typing import Any
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pysyswatch.config.settings import settings
from pysyswatch.core.exceptions import DatabaseError
from pysyswatch.database.models import Base

logger = logging.getLogger(__name__)

# Ensure proper connection args for SQLite to avoid thread access issues
connect_args: dict[str, Any] = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

try:
    engine = create_engine(
        settings.database_url, connect_args=connect_args, pool_pre_ping=True
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.critical(f"Failed to initialize database engine: {e}")
    raise DatabaseError(f"Database initialization failed: {e}")


def init_db() -> None:
    """Create missing tables without replacing an existing database.

    SQLAlchemy create_all is intentionally non-destructive: it does not drop
    tables or alter existing schemas. Keep the Docker ``dbdata`` volume mounted
    at the configured database path. Future schema changes should use explicit
    Alembic migrations rather than deleting or recreating this database.
    """
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database schema checked; existing data preserved.")
    except Exception as e:
        logger.error(f"Failed to create database schema: {e}")
        raise DatabaseError(f"Schema creation failed: {e}")


def get_db() -> Generator[Session, None, None]:
    """Generator providing a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
