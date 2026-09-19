import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings

logger = logging.getLogger("document_intelligence")

is_sqlite = "sqlite" in settings.async_database_url
engine_kwargs = {"echo": False, "future": True}
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
    })

engine = create_async_engine(
    settings.async_database_url,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base model providing standard UUID primary key and timestamp mixins."""
    pass


class TimestampMixin:
    """Reusable mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


async def init_database() -> None:
    """
    Initializes and verifies database schema.
    If PostgreSQL is not running locally, seamlessly falls back to local SQLite
    so the service runs without external infrastructure barriers.
    """
    global engine, AsyncSessionLocal
    import app.models  # Register models

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database schema initialized successfully on {engine.url.drivername}")
    except Exception as ex:
        logger.warning(
            f"Unable to connect to primary database ({ex}). "
            f"Falling back to local SQLite database for local development/evaluation."
        )
        fallback_url = "sqlite+aiosqlite:///./doc_intelligence.db"
        engine = create_async_engine(fallback_url, echo=False, future=True)
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Initialized local SQLite database (doc_intelligence.db).")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session and ensures proper closure."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
