from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from .models import Book
from .schemas import BookCreate, BookUpdate
from typing import List, Optional
import datetime
from ..auth.schemas import UserId
from ..auth.utils import AccessTokenBearer


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



async def create_book_views(db: AsyncSession, book_data: BookCreate,current_user:int) -> Book:
    """Create a new book"""
    print("cur-----------",current_user)
    try:
        db_book = Book(
            title=book_data.title,
            author=book_data.author,
            publisher=book_data.publisher,
            publish_date=book_data.publish_date,
            page_count=book_data.page_count,
            language=book_data.language,
            user_id=current_user
            )
        db.add(db_book)
        await db.commit()
        await db.refresh(db_book)
        return db_book
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"Database error in create_book: {str(e)}")
        raise e




async def get_book_by_id_views(db: AsyncSession, book_id: int) -> Optional[Book]:
    """Get a book by ID"""
    try:
        stmt = select(Book).where(Book.id == book_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        raise e



async def get_books_views(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Book]:
    """Get all books with pagination"""
    try:
        stmt = select(Book).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise e
    

async def get_my_book_view(db:AsyncSession,current_user):
    try:
        stmt=select(Book).where(Book.user_id==current_user)
        result= await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise e

async def get_books_by_author_views(db: AsyncSession, author: str) -> List[Book]:
    """Get books by author"""
    try:
        stmt = select(Book).where(Book.author.ilike(f"%{author}%"))
        result = await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise e

async def update_book_views(db: AsyncSession, book_id: int, book_update: BookUpdate) -> Optional[Book]:
    """Update a book"""
    try:
        # Get the book first
        book = await get_book_by_id_views(db, book_id)
        if not book:
            return None
        
        # Update only provided fields
        update_data = book_update.model_dump(exclude_unset=True)
        if update_data:
            update_data['updated_at'] = datetime.datetime.utcnow()
            stmt = update(Book).where(Book.id == book_id).values(**update_data)
            await db.execute(stmt)
            await db.commit()
            
            # Refresh and return updated book
            await db.refresh(book)
        
        return book
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

async def delete_book_views(db: AsyncSession, book_id: int) -> bool:
    """Delete a book"""
    try:
        book = await get_book_by_id_views(db, book_id)
        if not book:
            return False
        
        stmt = delete(Book).where(Book.id == book_id)
        await db.execute(stmt)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

async def get_books_count_views(db: AsyncSession) -> int:
    """Get total count of books"""
    try:
        stmt = select(Book).with_only_columns(Book.id)
        result = await db.execute(stmt)
        return len(result.scalars().all())
    except SQLAlchemyError as e:
        raise e
