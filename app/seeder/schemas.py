from __future__ import annotations

from pydantic import BaseModel, Field


class SeedRequest(BaseModel):
    roles: int = Field(3, ge=0)
    users: int = Field(10, ge=0)
    genres: int = Field(5, ge=0)
    books: int = Field(15, ge=0)
    reviews_per_book: int = Field(2, ge=0)


class SeedResponse(BaseModel):
    roles: int
    users: int
    genres: int
    books: int
    book_details: int
    book_reviews: int
