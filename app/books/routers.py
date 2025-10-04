from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List, NoReturn
from fastapi import Depends, HTTPException, status, APIRouter

from app.Database.session import get_db
from ..auth.utils import AccessTokenBearer
from .schemas import (
    BookCreate,
    BookDetailCreate,
    BookDetailResponse,
    BookDetailUpdate,
    BookResponse,
    BookReviewCreate,
    BookReviewResponse,
    BookReviewUpdate,
    BookUpdate,
    GenreCreate,
    GenreResponse,
    GenreUpdate,
)
from .views import (
    create_book_detail_views,
    create_book_review_views,
    create_book_views,
    create_genre_views,
    delete_book_detail_views,
    delete_book_review_views,
    delete_book_views,
    delete_genre_views,
    get_book_by_id_views,
    get_book_detail_views,
    get_book_review_views,
    get_books_by_author_views,
    get_books_count_views,
    get_books_views,
    get_genre_by_id_views,
    get_my_book_view,
    list_book_reviews_views,
    list_genres_views,
    patch_book_detail_views,
    patch_book_review_views,
    update_book_review_views,
    update_book_views,
    update_genre_views,
    upsert_book_detail_views,
)

book_router = APIRouter(
    prefix="/book",
)


def _raise_db_error(message: str, exc: SQLAlchemyError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message,
    ) from exc


@book_router.post(
    "/create/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Books"],
)
async def create_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    token_details: dict = Depends(AccessTokenBearer()),
):
    """Create a new book"""
    try:
        user_data = token_details
        user_id = user_data.get("user")["user_id"]
        return await create_book_views(db, book, current_user=user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while creating book", exc)


@book_router.get(
    "/all",
    response_model=List[BookResponse],
    tags=["Books"],
)
async def get_books(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # user_details=Depends(AccessTokenBearer())
):
    """Get all books with pagination"""
    try:
        return await get_books_views(db, skip=skip, limit=limit)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while fetching books", exc)
    

@book_router.get(
    "/mybooks/",
    response_model=List[BookResponse],
    tags=["Books"],
)
async def get_my_book(
    db:AsyncSession = Depends(get_db),
    current_user=Depends(AccessTokenBearer())
    ):
    user_id = current_user["user"]["user_id"]
    try:
        return await get_my_book_view(db, user_id)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while fetching your books", exc)
    



@book_router.get(
    "/{book_id}",
    response_model=BookResponse,
    tags=["Books"],
)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user_details=Depends(AccessTokenBearer())    #for authenticate
):
    """Get a book by ID"""
    try:
        book = await get_book_by_id_views(db, book_id)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while fetching book", exc)

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    return book

@book_router.get(
    "/books/author/{author}",
    response_model=List[BookResponse],
    tags=["Books"],
)
async def get_books_by_author(
    author: str,
    db: AsyncSession = Depends(get_db)
):
    """Get books by author"""
    try:
        return await get_books_by_author_views(db, author)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while fetching books by author", exc)

@book_router.put(
    "/books/{book_id}",
    response_model=BookResponse,
    tags=["Books"],
)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a book"""
    try:
        book = await update_book_views(db, book_id, book_update)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return book
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while updating book", exc)


@book_router.patch(
    "/books/{book_id}",
    response_model=BookResponse,
    tags=["Books"],
)
async def patch_book(
    book_id: int,
    book_update: BookUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Partially update a book."""
    try:
        book = await update_book_views(db, book_id, book_update)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )
        return book
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while updating book", exc)

@book_router.delete(
    "/books/{book_id}",
    tags=["Books"],
)
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a book"""
    try:
        success = await delete_book_views(db, book_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return {"message": "Book deleted successfully"}
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while deleting book", exc)

@book_router.get(
    "/books-count/",
    tags=["Books"],
)
async def get_books_count(db: AsyncSession = Depends(get_db)):
    """Get total count of books"""
    try:
        count = await get_books_count_views(db)
        return {"total_books": count}
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while counting books", exc)


@book_router.post(
    "/genres/",
    response_model=GenreResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Genres"],
)
async def create_genre(
    genre: GenreCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        return await create_genre_views(db, genre)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while creating genre", exc)


@book_router.get(
    "/genres/",
    response_model=List[GenreResponse],
    tags=["Genres"],
)
async def list_genres(
    db: AsyncSession = Depends(get_db),
):
    try:
        return await list_genres_views(db)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while fetching genres", exc)


@book_router.get(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    tags=["Genres"],
)
async def get_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
):
    genre_obj = await get_genre_by_id_views(db, genre_id)
    if not genre_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found",
        )
    return genre_obj


@book_router.put(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    tags=["Genres"],
)
async def replace_genre(
    genre_id: int,
    genre: GenreCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        updated = await update_genre_views(db, genre_id, GenreUpdate(**genre.model_dump()))
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Genre not found",
            )
        return updated
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while updating genre", exc)


@book_router.patch(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    tags=["Genres"],
)
async def patch_genre(
    genre_id: int,
    genre: GenreUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        updated = await update_genre_views(db, genre_id, genre)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Genre not found",
            )
        return updated
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while updating genre", exc)


@book_router.delete(
    "/genres/{genre_id}",
    tags=["Genres"],
)
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        deleted = await delete_genre_views(db, genre_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Genre not found",
            )
        return {"message": "Genre deleted successfully"}
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while deleting genre", exc)


@book_router.post(
    "/{book_id}/detail",
    response_model=BookDetailResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Book Details"],
)
async def create_book_detail(
    book_id: int,
    detail: BookDetailCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        created = await create_book_detail_views(db, book_id, detail)
        if not created:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )
        return created
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while creating book detail", exc)


@book_router.get(
    "/{book_id}/detail",
    response_model=BookDetailResponse,
    tags=["Book Details"],
)
async def get_book_detail(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    detail = await get_book_detail_views(db, book_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book detail not found",
        )
    return detail


@book_router.put(
    "/{book_id}/detail",
    response_model=BookDetailResponse,
    tags=["Book Details"],
)
async def replace_book_detail(
    book_id: int,
    detail: BookDetailCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        updated = await upsert_book_detail_views(db, book_id, detail)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )
        return updated
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while updating book detail", exc)


@book_router.patch(
    "/{book_id}/detail",
    response_model=BookDetailResponse,
    tags=["Book Details"],
)
async def patch_book_detail(
    book_id: int,
    detail: BookDetailUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        updated = await patch_book_detail_views(db, book_id, detail)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book detail not found",
            )
        return updated
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while updating book detail", exc)


@book_router.delete(
    "/{book_id}/detail",
    tags=["Book Details"],
)
async def delete_book_detail(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        deleted = await delete_book_detail_views(db, book_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book detail not found",
            )
        return {"message": "Book detail deleted successfully"}
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while deleting book detail", exc)


@book_router.post(
    "/{book_id}/reviews",
    response_model=BookReviewResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Reviews"],
)
async def create_book_review(
    book_id: int,
    review: BookReviewCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        created = await create_book_review_views(db, book_id, review)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while creating book review", exc)

    if not created:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return created


@book_router.get(
    "/{book_id}/reviews",
    response_model=List[BookReviewResponse],
    tags=["Reviews"],
)
async def list_book_reviews(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await list_book_reviews_views(db, book_id)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while fetching reviews", exc)


@book_router.get(
    "/{book_id}/reviews/{review_id}",
    response_model=BookReviewResponse,
    tags=["Reviews"],
)
async def get_book_review(
    book_id: int,
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    review_obj = await get_book_review_views(db, book_id, review_id)
    if not review_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return review_obj


@book_router.put(
    "/{book_id}/reviews/{review_id}",
    response_model=BookReviewResponse,
    tags=["Reviews"],
)
async def replace_book_review(
    book_id: int,
    review_id: int,
    review: BookReviewCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        updated = await update_book_review_views(db, book_id, review_id, review)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while updating book review", exc)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return updated


@book_router.patch(
    "/{book_id}/reviews/{review_id}",
    response_model=BookReviewResponse,
    tags=["Reviews"],
)
async def patch_book_review(
    book_id: int,
    review_id: int,
    review: BookReviewUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        updated = await patch_book_review_views(db, book_id, review_id, review)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while updating book review", exc)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return updated


@book_router.delete(
    "/{book_id}/reviews/{review_id}",
    tags=["Reviews"],
)
async def delete_book_review(
    book_id: int,
    review_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(AccessTokenBearer()),
):
    try:
        deleted = await delete_book_review_views(db, book_id, review_id)
    except SQLAlchemyError as exc:
        _raise_db_error("Database error while deleting book review", exc)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return {"message": "Review deleted successfully"}
