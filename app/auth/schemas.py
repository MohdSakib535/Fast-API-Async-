from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)



class RoleOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class meResponse(BaseModel):
    id: int
    name: str
    email: str
    role: RoleResponse  # Nested role object
    

    model_config = ConfigDict(from_attributes=True)

class meBookResponse(meResponse):
    books: Optional[List[BookBase]] = None

    model_config = ConfigDict(from_attributes=True)



class UserBase(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class UserWithRole(UserBase):
    role: Optional[RoleOut] = None


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
    
    model_config = ConfigDict(from_attributes=True)



class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str



class TokenData(BaseModel):
    email: Optional[str] = None
