from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GenreBase(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class GenreCreate(GenreBase):
    pass


class GenreUpdate(BaseModel):
    name: Optional[str] = None


class GenreResponse(GenreBase):
    id: int


class BookDetailBase(BaseModel):
    isbn: str
    summary: Optional[str] = None
    cover_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BookDetailCreate(BookDetailBase):
    pass


class BookDetailUpdate(BaseModel):
    isbn: Optional[str] = None
    summary: Optional[str] = None
    cover_image_url: Optional[str] = None


class BookDetailResponse(BookDetailBase):
    id: int
    book_id: int

class BookBase(BaseModel):
    title: str
    author: str
    publisher: str
    publish_date: date
    page_count: int
    language: str

    model_config = ConfigDict(from_attributes=True)


class BookCreate(BookBase):
    detail: Optional[BookDetailCreate] = None
    genre_ids: list[int] = Field(default_factory=list)

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[date] = None
    page_count: Optional[int] = None
    language: Optional[str] = None
    user_id: Optional[int] = None
    detail: Optional[BookDetailUpdate] = None
    genre_ids: Optional[list[int]] = None


class BookReviewBase(BaseModel):
    reviewer_name: str
    rating: int
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BookReviewCreate(BookReviewBase):
    pass


class BookReviewUpdate(BaseModel):
    reviewer_name: Optional[str] = None
    rating: Optional[int] = None
    comment: Optional[str] = None


class BookReviewResponse(BookReviewBase):
    id: int
    book_id: int
    created_at: datetime

class BookResponse(BookBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    detail: Optional[BookDetailResponse] = None
    genres: list[GenreResponse] = Field(default_factory=list)
    reviews: list[BookReviewResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
