from app.Database.session import Base
from sqlalchemy import Column,String,Integer,ForeignKey
from sqlalchemy.orm import relationship,mapped_column,Mapped
# from ..books.models import Book
from sqlalchemy import Enum as SQLAlchemyEnum
from enum import Enum as PyEnum  # Python enum




class Role(Base):

    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Relationship
    users: Mapped[list["User"]] = relationship(back_populates="role")





class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)


    role: Mapped["Role"] = relationship(back_populates="users")
    books: Mapped[list["Book"]] = relationship(back_populates="user")   # lazy='select' by default

    def __repr__(self)->str:
        return f"User(id={self.id!r},name={self.name!r})"