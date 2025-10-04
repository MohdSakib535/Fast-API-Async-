"""Utility helpers for seeding every relational table with fake data.

`run_seed` coordinates the creation of roles, users, genres, books, book details, and
reviews in a single transaction. Relationships are honoured (e.g. books belong to
users, details are one-to-one) while Faker supplies varied sample data. Callers receive
insert counts so they can see what was generated on each run.
"""

from __future__ import annotations

import random

from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Role, User
from app.auth.utils import Hash
from app.books.models import Book, BookDetail, BookReview, Genre
from .schemas import SeedRequest, SeedResponse


faker = Faker()


async def _load_all(session: AsyncSession, model: type) -> list:
    result = await session.execute(select(model))
    return list(result.scalars())


async def run_seed(session: AsyncSession, payload: SeedRequest) -> SeedResponse:
    counters = {
        "roles": 0,
        "users": 0,
        "genres": 0,
        "books": 0,
        "book_details": 0,
        "book_reviews": 0,
    }

    faker.unique.clear()

    existing_roles = await _load_all(session, Role)
    existing_genres = await _load_all(session, Genre)
    existing_users = await _load_all(session, User)

    new_roles: list[Role] = []
    for _ in range(payload.roles):
        role = Role(name=faker.unique.job()[:50])
        session.add(role)
        new_roles.append(role)
    if new_roles:
        await session.flush()
        counters["roles"] += len(new_roles)

    role_pool = existing_roles + new_roles
    if payload.users > 0 and not role_pool:
        raise ValueError("Cannot seed users without at least one role")

    new_users: list[User] = []
    for _ in range(payload.users):
        role = random.choice(role_pool)
        user = User(
            name=faker.name(),
            email=faker.unique.email(),
            password=Hash.bcrypt("Password123!"),
            role_id=role.id,
        )
        session.add(user)
        new_users.append(user)
    if new_users:
        await session.flush()
        counters["users"] += len(new_users)

    user_pool = existing_users + new_users
    if payload.books > 0 and not user_pool:
        raise ValueError("Cannot seed books without at least one user")

    new_genres: list[Genre] = []
    for _ in range(payload.genres):
        genre = Genre(name=faker.unique.word().title())
        session.add(genre)
        new_genres.append(genre)
    if new_genres:
        await session.flush()
        counters["genres"] += len(new_genres)

    genre_pool = existing_genres + new_genres
    if payload.books > 0 and not genre_pool:
        raise ValueError("Cannot seed books without at least one genre")

    faker.unique.clear()

    for _ in range(payload.books):
        owner = random.choice(user_pool)
        book = Book(
            title=faker.sentence(nb_words=5).rstrip('.'),
            author=faker.name(),
            publisher=faker.company(),
            publish_date=faker.date_between(start_date="-10y", end_date="today"),
            page_count=random.randint(90, 800),
            language=random.choice(["English", "Spanish", "French", "German", "Hindi"]),
            user_id=owner.id,
        )

        book.genres = random.sample(
            genre_pool,
            k=min(len(genre_pool), max(1, random.randint(1, min(len(genre_pool), 3)))),
        )

        session.add(book)
        await session.flush()
        counters["books"] += 1

        detail = BookDetail(
            book_id=book.id,
            isbn=faker.unique.isbn13(separator=""),
            summary=faker.paragraph(nb_sentences=3),
            cover_image_url=faker.image_url(),
        )
        session.add(detail)
        counters["book_details"] += 1

        reviews_to_create = payload.reviews_per_book
        for _ in range(reviews_to_create):
            review = BookReview(
                book_id=book.id,
                reviewer_name=faker.name(),
                rating=random.randint(1, 5),
                comment=faker.paragraph(nb_sentences=2),
            )
            session.add(review)
            counters["book_reviews"] += 1

    await session.commit()

    return SeedResponse(**counters)
