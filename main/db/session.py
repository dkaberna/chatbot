"""
Database session and engine setup for async SQLAlchemy.

This module provides:
- An async SQLAlchemy engine using `create_async_engine`
- A session factory (`SessionLocal`) using `AsyncSession`
- A FastAPI dependency function `get_db` to inject database sessions into routes

Requirements:
- The `DATABASE_URL` must use the `postgresql+asyncpg://` scheme
- All downstream consumers should use `AsyncSession` and `await` patterns

Note:
- This configuration is intended for use with FastAPI and asynchronous services.
- `SessionLocal` should be injected via FastAPI's `Depends()` to ensure proper lifespan handling.
"""

from typing import Generator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from main.core.config import get_app_settings

# Load environment-specific settings
settings = get_app_settings()

# Create an asynchronous engine (e.g. for PostgreSQL using asyncpg)
engine = create_async_engine(
    url=settings.database_url,  # Must be of the form: postgresql+asyncpg://user:pass@host/dbname
    echo=True,                  # Enables SQL echo for debugging
    future=True                 # Uses 2.0 SQLAlchemy execution model
)

# Create session factory using the async engine and AsyncSession
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db() -> Generator:
    """
    FastAPI dependency that yields an AsyncSession.
    
    Ensures each request gets a new session and closes it after use.

    Usage:
        @router.get("/example")
        async def example_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
