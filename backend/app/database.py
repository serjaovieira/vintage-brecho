"""
Database connection and session management module for Vintage Brechó.
Configured for Supabase PostgreSQL pooler using asyncpg with statement_cache_size=0,
with automatic SQLite fallback for testing and offline environments.
"""

import logging
import os
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger("vintage_brecho.database")


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Declarative Base."""
    pass


def _build_engine(db_url: str):
    connect_args = {}
    is_sqlite = "sqlite" in db_url
    if "postgresql" in db_url or "asyncpg" in db_url:
        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        }
    elif is_sqlite:
        connect_args = {
            "check_same_thread": False,
        }

    return create_async_engine(
        db_url,
        echo=settings.DB_ECHO,
        pool_size=5 if is_sqlite else settings.DB_POOL_SIZE,
        max_overflow=10 if is_sqlite else settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=connect_args,
    )


_primary_engine = _build_engine(settings.async_database_url)
_fallback_engine = _build_engine("sqlite+aiosqlite:///brecho.db")

_use_fallback = False
_active_engine = _primary_engine

engine = _primary_engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session.
    Automatically handles rollback on exception, session closure,
    and falls back to SQLite if primary PostgreSQL is unreachable.
    """
    global _use_fallback, _active_engine

    if _use_fallback:
        maker = async_sessionmaker(
            bind=_fallback_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
        return

    # Attempt primary connection
    maker = async_sessionmaker(
        bind=_primary_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    try:
        async with maker() as session:
            # Probe connection vitality
            await session.execute(text("SELECT 1"))
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    except Exception as exc:
        logger.warning(
            f"Conexão com PostgreSQL falhou ({exc}). "
            f"Ativando fallback local para SQLite 'sqlite+aiosqlite:///brecho.db'."
        )
        _use_fallback = True
        _active_engine = _fallback_engine

        try:
            from app.models import Product, Order
        except ImportError:
            from backend.app.models import Product, Order

        # Ensure fallback schema exists
        async with _fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        fallback_maker = async_sessionmaker(
            bind=_fallback_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with fallback_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


async def init_db() -> None:
    """
    Idempotent schema creation on application startup.
    Runs Base.metadata.create_all within an async transaction.
    Falls back gracefully to SQLite if the remote PostgreSQL database is unreachable.
    """
    global _use_fallback, _active_engine, engine
    try:
        from app.models import Product, Order
    except ImportError:
        from backend.app.models import Product, Order

    try:
        async with _primary_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database schema initialized successfully on PostgreSQL.")
    except Exception as exc:
        logger.warning(
            f"Could not connect to primary PostgreSQL ({exc}). "
            f"Activating fallback to local SQLite 'sqlite+aiosqlite:///brecho.db'."
        )
        _use_fallback = True
        _active_engine = _fallback_engine
        engine = _fallback_engine
        async with _fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Local SQLite database initialized as active fallback.")


async def dispose_engines() -> None:
    """Closes all underlying connection pools cleanly."""
    await _primary_engine.dispose()
    await _fallback_engine.dispose()
