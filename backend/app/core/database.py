from __future__ import annotations

import asyncio
from typing import AsyncGenerator, AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import logger

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    pass


Base.metadata.naming_convention = naming_convention  # type: ignore


def _get_async_url(url: str) -> str:
    """Ensure the database URL uses the asyncpg driver."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        logger.info("database.url_upgraded_to_asyncpg")
        return async_url
    return url


async_db_url = _get_async_url(settings.supabase_db_url)

engine = create_async_engine(
    async_db_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"timeout": 10},
    json_serializer=lambda obj: __import__("json").dumps(obj, default=str),
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


async def check_database_health() -> bool:
    try:
        async with async_session_factory() as session:
            await asyncio.wait_for(
                session.execute(__import__("sqlalchemy").text("SELECT 1")),
                timeout=5.0,
            )
            return True
    except asyncio.TimeoutError:
        logger.warning("database.health_check_timed_out")
        return False
    except Exception as exc:
        logger.warning("database.health_check_failed", error=str(exc))
        return False
