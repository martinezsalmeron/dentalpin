"""Database configuration and session management."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings

# Create async engine with connection pool settings.
#
# ``pool_pre_ping`` issues a cheap ``SELECT 1`` before checking out a
# connection so stale sockets (DB restart, NAT/firewall idle drop) are
# transparently recycled instead of failing the next request with a
# generic "connection lost". ``pool_recycle=3600`` ages connections out
# proactively so we don't accumulate idle ones a proxy might silently
# close.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=settings.ENVIRONMENT == "development",
)

# ``expire_on_commit=False`` keeps ORM objects hydrated after a commit
# so the router can serialise the response without an extra refresh
# round-trip. Anything streaming or kept across awaits (long-lived
# tasks, websockets) must re-fetch explicitly — but the request-scoped
# pattern that dominates the codebase relies on this.
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables. For development only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
