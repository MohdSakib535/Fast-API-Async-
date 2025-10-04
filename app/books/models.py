from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.Database.session import Base
from ..auth.models import User


# Association table for the many-to-many relationship between books and genres
book_genre_association = Table(
    "book_genre_association",
    Base.metadata,
    Column("book_id", ForeignKey("book.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    books: Mapped[list["Book"]] = relationship(
        secondary=book_genre_association,
        back_populates="genres",
    )


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    publisher: Mapped[str] = mapped_column(String, nullable=False)
    publish_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    page_count: Mapped[int] = mapped_column(nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="books")
    detail: Mapped[Optional["BookDetail"]] = relationship(
        back_populates="book",
        uselist=False,
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["BookReview"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )
    genres: Mapped[list["Genre"]] = relationship(
        secondary=book_genre_association,
        back_populates="books",
    )


class BookDetail(Base):
    """Stores one-to-one metadata for a book."""

    __tablename__ = "book_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"), unique=True)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    book: Mapped["Book"] = relationship(back_populates="detail")


class BookReview(Base):
    __tablename__ = "book_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"), index=True)
    reviewer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)

    book: Mapped["Book"] = relationship(back_populates="reviews")
