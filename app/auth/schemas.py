from pydantic import BaseModel
from typing import Optional,List
from ..books.schemas import BookBase

class UserId(BaseModel):
    id:int


class UserLoginModel(BaseModel):
    email: str
    password: str

class CreateUser(BaseModel):
    name: str
    email: str
    password: str
    role:int


class CreateRole(BaseModel):
    name:str


class RoleResponse(CreateRole):
    id:int

    class Config:
        from_attributes = True



class RoleOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class meResponse(BaseModel):
    id: int
    name: str
    email: str
    role: RoleResponse  # Nested role object
    

    class Config:
        from_attributes = True

class meBookResponse(meResponse):
    books: Optional[List[BookBase]] = None

    class Config:
        from_attributes = True



class UserBase(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class UserWithRole(UserBase):
    role: RoleOut | None


class AssignRole(BaseModel):
    role_id: int


    
class Getuser(BaseModel):
    id:int
    name:str
    email:str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role_id:int
    
    class Config:
        from_attributes = True



class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str



class TokenData(BaseModel):
    email: Optional[str] = None