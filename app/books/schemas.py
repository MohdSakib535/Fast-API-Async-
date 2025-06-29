from pydantic import BaseModel
from datetime import date,datetime
from typing import Optional

class BookBase(BaseModel):
    title: str
    author: str
    publisher: str
    publish_date: date
    page_count: int
    language: str

    class Config:
        from_attributes = True


class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[date] = None
    page_count: Optional[int] = None
    language: Optional[str] = None
    user_id:Optional[int]=None

class BookResponse(BookBase):
    id: int
    user_id:Optional[int]=None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True