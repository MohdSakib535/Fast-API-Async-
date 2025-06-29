from sqlalchemy.ext.asyncio import AsyncSession
from app.Database.session import get_db,engine
from typing import List
from fastapi import Depends,HTTPException,status,APIRouter
from .views import create_book_views,get_book_by_id_views,get_books_views,get_books_by_author_views,get_books_count_views,update_book_views,delete_book_views,get_my_book_view
from .schemas import BookResponse,BookCreate,BookUpdate
from ..auth.schemas import CreateUser
from ..auth.utils import AccessTokenBearer

book_router = APIRouter(
    prefix="/book",
    tags=["Books"]
)


@book_router.post("/create/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    token_details: dict = Depends(AccessTokenBearer()),
    # current_user:CreateUser=Depends(get_current_user)
):
    """Create a new book"""
    user_data=token_details
    user_id=user_data.get("user")['user_id']
    return await create_book_views(db, book,current_user=user_id)
    
    # try:
    #     user_data=token_details
    #     user_id=user_data.get("user")['user_id']
    #     # print("--userdata-----",user_data.get("user")['user_id'])
    #     return await create_book_views(db, book,current_user=user_id)
    # except Exception as e:
    #     print(f"Error creating book: {e.__class__.__name__}: {e}")
    #     raise HTTPException(
            
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"Failed to create book: {type(e).__name__}"
    #     )
    


@book_router.get("/all", response_model=List[BookResponse])
async def get_books(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_details=Depends(AccessTokenBearer())
):
    """Get all books with pagination"""
    try:
        books = await get_books_views(db, skip=skip, limit=limit)
        return books
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching books: {str(e)}"
        )
    

@book_router.get("/mybooks/",response_model=List[BookResponse])
async def get_my_book(
    db:AsyncSession = Depends(get_db),
    current_user=Depends(AccessTokenBearer())
    ):
    try:
        user_id=current_user["user"]["user_id"]
        book=await get_my_book_view(db,user_id)
        return book
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching books: {str(e)}"
        )
    



@book_router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user_details=Depends(AccessTokenBearer())    #for authenticate
):
    """Get a book by ID"""
    try:
        book = await get_book_by_id_views(db, book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return book
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching book: {str(e)}"
        )

@book_router.get("/books/author/{author}", response_model=List[BookResponse])
async def get_books_by_author(
    author: str,
    db: AsyncSession = Depends(get_db)
):
    """Get books by author"""
    try:
        books = await get_books_by_author_views(db, author)
        return books
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching books by author: {str(e)}"
        )

@book_router.put("/books/{book_id}", response_model=BookResponse)
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating book: {str(e)}"
        )

@book_router.delete("/books/{book_id}")
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting book: {str(e)}"
        )

@book_router.get("/books-count/")
async def get_books_count(db: AsyncSession = Depends(get_db)):
    """Get total count of books"""
    try:
        count = await get_books_count_views(db)
        return {"total_books": count}
    except Exception as e:
        print(f"Error creating book: {e.__class__.__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting books count: {type(e).__name__}"
        )