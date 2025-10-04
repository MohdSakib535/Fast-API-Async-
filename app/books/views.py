from __future__ import annotations

import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Book, BookDetail, BookReview, Genre
from .schemas import (
    BookCreate,
    BookDetailCreate,
    BookDetailUpdate,
    BookReviewCreate,
    BookReviewUpdate,
    BookUpdate,
    GenreCreate,
    GenreUpdate,
)


# async def create_book_views(db: AsyncSession, book_data: BookCreate,curr) -> Book:
#     """Create a new book"""
#     try:
#         db_book = Book(**book_data.model_dump())
#         db.add(db_book)
#         await db.commit()
#         await db.refresh(db_book)
#         return db_book
#     except SQLAlchemyError as e:
#         await db.rollback()
#         print(f"Database error in create_book: {str(e)}")
#         raise e

async def _load_genres(db: AsyncSession, genre_ids: Sequence[int]) -> list[Genre]:
    if not genre_ids:
        return []

    stmt = select(Genre).where(Genre.id.in_(genre_ids))
    result = await db.execute(stmt)
    genres = result.scalars().all()

    found_ids = {genre.id for genre in genres}
    missing = set(genre_ids) - found_ids
    if missing:
        missing_str = ", ".join(str(genre_id) for genre_id in sorted(missing))
        raise ValueError(f"Unknown genre id(s): {missing_str}")

    return genres


async def create_book_views(db: AsyncSession, book_data: BookCreate, current_user: int) -> Book:
    """Create a new book"""
    try:
        db_book = Book(
            title=book_data.title,
            author=book_data.author,
            publisher=book_data.publisher,
            publish_date=book_data.publish_date,
            page_count=book_data.page_count,
            language=book_data.language,
            user_id=current_user,
        )

        if book_data.detail:
            db_book.detail = BookDetail(**book_data.detail.model_dump())

        db_book.genres = await _load_genres(db, book_data.genre_ids)

        db.add(db_book)
        await db.commit()

        return await get_book_by_id_views(db, db_book.id)
    except ValueError as exc:
        await db.rollback()
        raise exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc




async def get_book_by_id_views(db: AsyncSession, book_id: int) -> Optional[Book]:
    """Get a book by ID"""
    stmt = (
        select(Book)
        .options(
            selectinload(Book.detail),
            selectinload(Book.reviews),
            selectinload(Book.genres),
        )
        .where(Book.id == book_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()



async def get_books_views(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Book]:
    """Get all books with pagination"""
    stmt = (
        select(Book)
        .options(
            selectinload(Book.detail),
            selectinload(Book.reviews),
            selectinload(Book.genres),
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_my_book_view(db: AsyncSession, current_user: int) -> list[Book]:
    stmt = (
        select(Book)
        .options(
            selectinload(Book.detail),
            selectinload(Book.reviews),
            selectinload(Book.genres),
        )
        .where(Book.user_id == current_user)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_books_by_author_views(db: AsyncSession, author: str) -> list[Book]:
    """Get books by author"""
    stmt = (
        select(Book)
        .options(
            selectinload(Book.detail),
            selectinload(Book.reviews),
            selectinload(Book.genres),
        )
        .where(Book.author.ilike(f"%{author}%"))
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_book_views(db: AsyncSession, book_id: int, book_update: BookUpdate) -> Optional[Book]:
    """Update a book"""
    try:
        # Get the book first
        book = await get_book_by_id_views(db, book_id)
        if not book:
            return None
        
        update_data = book_update.model_dump(exclude_unset=True)
        detail_data = update_data.pop("detail", None)
        genre_ids = update_data.pop("genre_ids", None)

        for field, value in update_data.items():
            setattr(book, field, value)

        if detail_data is not None:
            if book.detail is None:
                if detail_data.get("isbn") is None:
                    raise ValueError("isbn is required to create a book detail")
                book.detail = BookDetail(**BookDetailCreate(**detail_data).model_dump())
            else:
                for field, value in detail_data.items():
                    if value is not None:
                        setattr(book.detail, field, value)

        if genre_ids is not None:
            book.genres = await _load_genres(db, genre_ids)

        book.updated_at = datetime.datetime.utcnow()

        await db.commit()

        return await get_book_by_id_views(db, book_id)
    except ValueError as exc:
        await db.rollback()
        raise exc
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

async def delete_book_views(db: AsyncSession, book_id: int) -> bool:
    """Delete a book"""
    try:
        book = await get_book_by_id_views(db, book_id)
        if not book:
            return False

        await db.delete(book)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

async def get_books_count_views(db: AsyncSession) -> int:
    """Get total count of books"""
    stmt = select(Book.id)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def create_genre_views(db: AsyncSession, genre_data: GenreCreate) -> Genre:
    try:
        genre = Genre(**genre_data.model_dump())
        db.add(genre)
        await db.commit()
        await db.refresh(genre)
        return genre
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def list_genres_views(db: AsyncSession) -> list[Genre]:
    result = await db.execute(select(Genre))
    return result.scalars().all()


async def get_genre_by_id_views(db: AsyncSession, genre_id: int) -> Optional[Genre]:
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    return result.scalar_one_or_none()


async def update_genre_views(db: AsyncSession, genre_id: int, genre_data: GenreUpdate) -> Optional[Genre]:
    try:
        genre = await get_genre_by_id_views(db, genre_id)
        if not genre:
            return None

        update_data = genre_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(genre, field, value)

        await db.commit()
        await db.refresh(genre)
        return genre
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def delete_genre_views(db: AsyncSession, genre_id: int) -> bool:
    try:
        genre = await get_genre_by_id_views(db, genre_id)
        if not genre:
            return False

        await db.delete(genre)
        await db.commit()
        return True
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def create_book_detail_views(
    db: AsyncSession, book_id: int, detail_data: BookDetailCreate
) -> Optional[BookDetail]:
    try:
        book = await get_book_by_id_views(db, book_id)
        if not book:
            return None
        if book.detail is not None:
            raise ValueError("Book already has detail information")

        detail = BookDetail(book_id=book_id, **detail_data.model_dump())
        db.add(detail)
        await db.commit()
        await db.refresh(detail)
        return detail
    except ValueError as exc:
        await db.rollback()
        raise exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def get_book_detail_views(db: AsyncSession, book_id: int) -> Optional[BookDetail]:
    try:
        result = await db.execute(
            select(BookDetail).where(BookDetail.book_id == book_id)
        )
        return result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise exc


async def upsert_book_detail_views(
    db: AsyncSession, book_id: int, detail_data: BookDetailCreate
) -> Optional[BookDetail]:
    """Replace the current detail (PUT semantics)."""

    existing = await get_book_detail_views(db, book_id)
    if existing:
        for field, value in detail_data.model_dump().items():
            setattr(existing, field, value)
        try:
            await db.commit()
            await db.refresh(existing)
            return existing
        except SQLAlchemyError as exc:
            await db.rollback()
            raise exc

    return await create_book_detail_views(db, book_id, detail_data)


async def patch_book_detail_views(
    db: AsyncSession, book_id: int, detail_data: BookDetailUpdate
) -> Optional[BookDetail]:
    try:
        detail = await get_book_detail_views(db, book_id)
        if not detail:
            return None

        update_data = detail_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(detail, field, value)

        await db.commit()
        await db.refresh(detail)
        return detail
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def delete_book_detail_views(db: AsyncSession, book_id: int) -> bool:
    try:
        detail = await get_book_detail_views(db, book_id)
        if not detail:
            return False

        await db.delete(detail)
        await db.commit()
        return True
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def create_book_review_views(
    db: AsyncSession, book_id: int, review_data: BookReviewCreate
) -> Optional[BookReview]:
    try:
        book = await get_book_by_id_views(db, book_id)
        if not book:
            return None

        review = BookReview(book_id=book_id, **review_data.model_dump())
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def list_book_reviews_views(db: AsyncSession, book_id: int) -> list[BookReview]:
    result = await db.execute(
        select(BookReview).where(BookReview.book_id == book_id)
    )
    return result.scalars().all()


async def get_book_review_views(
    db: AsyncSession, book_id: int, review_id: int
) -> Optional[BookReview]:
    result = await db.execute(
        select(BookReview)
        .where(BookReview.book_id == book_id)
        .where(BookReview.id == review_id)
    )
    return result.scalar_one_or_none()


async def update_book_review_views(
    db: AsyncSession, book_id: int, review_id: int, review_data: BookReviewCreate
) -> Optional[BookReview]:
    review = await get_book_review_views(db, book_id, review_id)
    if not review:
        return None

    try:
        for field, value in review_data.model_dump().items():
            setattr(review, field, value)

        await db.commit()
        await db.refresh(review)
        return review
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def patch_book_review_views(
    db: AsyncSession, book_id: int, review_id: int, review_data: BookReviewUpdate
) -> Optional[BookReview]:
    review = await get_book_review_views(db, book_id, review_id)
    if not review:
        return None

    try:
        update_data = review_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)

        await db.commit()
        await db.refresh(review)
        return review
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc


async def delete_book_review_views(
    db: AsyncSession, book_id: int, review_id: int
) -> bool:
    review = await get_book_review_views(db, book_id, review_id)
    if not review:
        return False

    try:
        await db.delete(review)
        await db.commit()
        return True
    except SQLAlchemyError as exc:
        await db.rollback()
        raise exc
