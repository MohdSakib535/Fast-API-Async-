from app.Database.session import Base
from sqlalchemy import Column,String,DateTime,Integer,Date,ForeignKey
import datetime
from ..auth.models import User
from sqlalchemy.orm import relationship,mapped_column,Mapped

class Book(Base):
    __tablename__="book"

    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    title:Mapped[str]=mapped_column(nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    publisher: Mapped[str] = mapped_column(String, nullable=False)
    publish_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    page_count: Mapped[int] = mapped_column(nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)



    user_id:Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="books")
