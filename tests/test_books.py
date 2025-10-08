from __future__ import annotations

import pytest
from sqlalchemy import select

from app.books.models import Book, Genre, BookDetail, BookReview
from app.books.schemas import (
    BookDetailCreate,
    BookDetailUpdate,
    BookReviewCreate,
    BookReviewUpdate,
    GenreCreate,
    GenreUpdate,
)
from app.books.views import (
    create_book_detail_views,
    create_book_review_views,
    create_book_views,
    create_genre_views,
    delete_book_detail_views,
    delete_book_review_views,
    delete_genre_views,
    get_book_by_id_views,
    get_book_detail_views,
    get_book_review_views,
    get_books_views,
    get_genre_by_id_views,
    list_book_reviews_views,
    patch_book_detail_views,
    patch_book_review_views,
    update_book_review_views,
    update_genre_views,
)


@pytest.mark.asyncio
async def test_create_book_views_persists_book_with_detail(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory()

    created_book = await create_book_views(db_session, book_payload, current_user=user_id)

    assert created_book.id is not None
    assert created_book.detail is not None
    assert created_book.detail.isbn == "ISBN-1234567890"
    assert len(created_book.genres) == 1
    assert created_book.genres[0].name == "Test Genre"

    result = await db_session.execute(select(Book).where(Book.id == created_book.id))
    stored_book = result.scalar_one()
    assert stored_book.title == "Demo Book"
    assert stored_book.user_id == user_id


@pytest.mark.asyncio
async def test_get_books_views_returns_only_created_books(db_session, book_payload_factory):
    additional_genre = Genre(name="Adventure")
    db_session.add(additional_genre)
    await db_session.flush()

    first_book, user_id = book_payload_factory(
        title="The First Quest",
        author="Author One",
        publisher="Quest Press",
        page_count=280,
        include_detail=False,
    )

    second_book, _ = book_payload_factory(
        title="Adventures Beyond",
        author="Author Two",
        publisher="Adventure House",
        page_count=310,
        include_detail=False,
        genre_ids=[additional_genre.id],
    )

    await create_book_views(db_session, first_book, current_user=user_id)
    await create_book_views(db_session, second_book, current_user=user_id)

    books = await get_books_views(db_session, skip=0, limit=10)

    assert len(books) == 2
    titles = sorted(book.title for book in books)
    assert titles == ["Adventures Beyond", "The First Quest"]


@pytest.mark.asyncio
async def test_create_book_views_raises_for_unknown_genre(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory(
        title="Mystery Without Genre",
        author="Unknown Author",
        publisher="Mystery Press",
        page_count=150,
        include_detail=False,
        genre_ids=[9999],
    )

    with pytest.raises(ValueError, match="Unknown genre id"):
        await create_book_views(db_session, book_payload, current_user=user_id)


@pytest.mark.asyncio
async def test_create_genre_views_persists_genre(db_session):
    genre = await create_genre_views(db_session, GenreCreate(name="Science Fiction"))
    assert genre.id is not None
    stored = await get_genre_by_id_views(db_session, genre.id)
    assert stored is not None
    assert stored.name == "Science Fiction"


@pytest.mark.asyncio
async def test_update_genre_views_updates_name(db_session, persisted_genre):
    updated = await update_genre_views(db_session, persisted_genre.id, GenreUpdate(name="Updated Genre"))
    assert updated is not None
    assert updated.name == "Updated Genre"


@pytest.mark.asyncio
async def test_delete_genre_views_removes_genre(db_session):
    genre = await create_genre_views(db_session, GenreCreate(name="Temporary Genre"))
    deleted = await delete_genre_views(db_session, genre.id)
    assert deleted is True
    assert await get_genre_by_id_views(db_session, genre.id) is None


@pytest.mark.asyncio
async def test_create_book_detail_views_adds_detail(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory(include_detail=False)
    book = await create_book_views(db_session, book_payload, current_user=user_id)

    detail_data = BookDetailCreate(
        isbn="NEW-ISBN-001",
        summary="A brand new summary.",
        cover_image_url="https://example.com/new.jpg",
    )
    detail = await create_book_detail_views(db_session, book.id, detail_data)

    assert detail is not None
    assert detail.book_id == book.id
    stored = await get_book_detail_views(db_session, book.id)
    assert stored is not None
    assert stored.isbn == "NEW-ISBN-001"


@pytest.mark.asyncio
async def test_create_book_detail_views_raises_when_existing(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory()
    book = await create_book_views(db_session, book_payload, current_user=user_id)

    with pytest.raises(ValueError, match="already has detail"):
        await create_book_detail_views(
            db_session,
            book.id,
            BookDetailCreate(
                isbn="DUPLICATE-ISBN",
                summary="Duplicate summary",
                cover_image_url="https://example.com/dup.jpg",
            ),
        )


@pytest.mark.asyncio
async def test_patch_book_detail_views_updates_summary(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory()
    book = await create_book_views(db_session, book_payload, current_user=user_id)

    patched = await patch_book_detail_views(
        db_session,
        book.id,
        BookDetailUpdate(summary="Updated summary"),
    )

    assert patched is not None
    assert patched.summary == "Updated summary"


@pytest.mark.asyncio
async def test_delete_book_detail_views_removes_detail(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory()
    book = await create_book_views(db_session, book_payload, current_user=user_id)

    deleted = await delete_book_detail_views(db_session, book.id)
    assert deleted is True
    assert await get_book_detail_views(db_session, book.id) is None


@pytest.mark.asyncio
async def test_create_book_review_views_persists_review(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory(include_detail=False)
    book = await create_book_views(db_session, book_payload, current_user=user_id)

    review = await create_book_review_views(
        db_session,
        book.id,
        BookReviewCreate(reviewer_name="Alice", rating=5, comment="Loved it"),
    )

    assert review is not None
    assert review.book_id == book.id
    reviews = await list_book_reviews_views(db_session, book.id)
    assert len(reviews) == 1
    assert reviews[0].reviewer_name == "Alice"


@pytest.mark.asyncio
async def test_update_book_review_views_replaces_fields(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory(include_detail=False)
    book = await create_book_views(db_session, book_payload, current_user=user_id)

    review = await create_book_review_views(
        db_session,
        book.id,
        BookReviewCreate(reviewer_name="Bob", rating=3, comment="It was ok"),
    )

    updated = await update_book_review_views(
        db_session,
        book.id,
        review.id,
        BookReviewCreate(reviewer_name="Bob", rating=4, comment="Actually better"),
    )

    assert updated is not None
    assert updated.rating == 4
    assert updated.comment == "Actually better"


@pytest.mark.asyncio
async def test_patch_book_review_views_partial_update(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory(include_detail=False)
    book = await create_book_views(db_session, book_payload, current_user=user_id)

    review = await create_book_review_views(
        db_session,
        book.id,
        BookReviewCreate(reviewer_name="Charlie", rating=2, comment="Not great"),
    )

    patched = await patch_book_review_views(
        db_session,
        book.id,
        review.id,
        BookReviewUpdate(rating=3),
    )

    assert patched is not None
    assert patched.rating == 3
    assert patched.comment == "Not great"


@pytest.mark.asyncio
async def test_delete_book_review_views_removes_review(db_session, book_payload_factory):
    book_payload, user_id = book_payload_factory(include_detail=False)
    book = await create_book_views(db_session, book_payload, current_user=user_id)

    review = await create_book_review_views(
        db_session,
        book.id,
        BookReviewCreate(reviewer_name="Dana", rating=5, comment="Fantastic"),
    )

    deleted = await delete_book_review_views(db_session, book.id, review.id)
    assert deleted is True
    remaining = await list_book_reviews_views(db_session, book.id)
    assert remaining == []
