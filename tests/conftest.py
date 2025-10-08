from __future__ import annotations

import asyncio
import datetime
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.Database.session import Base

# Import models so SQLAlchemy registers table metadata on Base
import app.auth.models  # noqa: F401
import app.books.models  # noqa: F401
from app.auth.models import Role, User
from app.books.models import Genre
from app.books.schemas import BookCreate, BookDetailCreate


@pytest_asyncio.fixture
async def async_engine():
    """Create a shared in-memory SQLite async engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a new database session for each test against a dedicated engine."""
    async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def persisted_user(db_session: AsyncSession) -> User:
    """Create and persist a default user with role for tests."""
    role = Role(name="tester")
    user = User(
        name="Test User",
        email="test-user@example.com",
        password="hashed-password",
        role=role,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def persisted_genre(db_session: AsyncSession) -> Genre:
    """Create and persist a default genre for tests."""
    genre = Genre(name="Test Genre")
    db_session.add(genre)
    await db_session.flush()
    return genre


@pytest.fixture
def book_payload_factory(persisted_genre, persisted_user):
    """Return a factory that builds BookCreate payloads with sensible defaults."""

    def _factory(
        *,
        title: str = "Demo Book",
        author: str = "Jane Doe",
        publisher: str = "Future Press",
        publish_date: datetime.date | None = None,
        page_count: int = 320,
        language: str = "English",
        include_detail: bool = True,
        genre_ids: list[int] | None = None,
    ) -> tuple[BookCreate, int]:
        publish_date_value = publish_date or datetime.date.today()
        detail_obj = (
            BookDetailCreate(
                isbn="ISBN-1234567890",
                summary="Exploring distant galaxies.",
                cover_image_url="https://example.com/covers/demo-book.jpg",
            )
            if include_detail
            else None
        )
        effective_genre_ids = genre_ids if genre_ids is not None else [persisted_genre.id]

        payload = BookCreate(
            title=title,
            author=author,
            publisher=publisher,
            publish_date=publish_date_value,
            page_count=page_count,
            language=language,
            detail=detail_obj,
            genre_ids=effective_genre_ids,
        )
        return payload, persisted_user.id

    return _factory
