"""
MySQL engine and session factory (SQLAlchemy 2 async).
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

_settings = get_settings()

engine = create_async_engine(
    _settings.mysql_dsn,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=_settings.app_debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # FastAPI dependency
    async with AsyncSessionLocal() as session:
        yield session


async def create_all_tables() -> None:
    """Create all ORM-mapped tables (dev/test only; use Alembic in prod)."""
    from app.db.models import user, case, alert_assignment, audit_log  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
