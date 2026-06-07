"""
SAGE - Database connection management.

Sets up the SQLite database using SQLAlchemy's async engine.
SQLite is a single-file database (data/sage.db) - no server needed.

Owner: Tanjid (Backend) - scaffolded by Abrar
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# Load settings from the .env file
load_dotenv()

# Where the database lives. Defaults to data/sage.db inside the project.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./data/sage.db"
)

# Make sure the data/ folder exists before we try to write the DB file
Path("./data").mkdir(exist_ok=True)


# All our table models will inherit from this Base class.
class Base(DeclarativeBase):
    pass


# The "engine" is the core connection to the database.
# echo=True prints the SQL commands so we can see what's happening (helpful while learning).
engine = create_async_engine(DATABASE_URL, echo=True)

# A "session" is how we run queries. This factory creates them on demand.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """
    Provides a database session to whoever needs it (e.g. API endpoints).
    Automatically closes the session when done.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """
    Creates all database tables based on our models.
    Run this once at startup. Safe to run repeatedly - it won't
    overwrite existing tables.
    """
    # Import models here so they're registered with Base before table creation
    from backend.database import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)