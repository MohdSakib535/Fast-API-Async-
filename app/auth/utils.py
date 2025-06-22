from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer,HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from ..Database.session import get_db
from fastapi import Depends,HTTPException,status
from sqlalchemy import select
from .models import User
from .security import *
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login/")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
class Hash:
    @staticmethod
    def bcrypt(password: str) ->str:
        hassed_psw = pwd_context.hash(password)
        return hassed_psw
    
    @staticmethod
    def verify_password(hashed_password,plain_password):
        data=pwd_context.verify(plain_password,hashed_password)
        return data
    



async def get_current_user(token_details:dict=Depends(AccessTokenBearer()),db:AsyncSession=Depends(get_db)):

    from .views import UserService
    user_service = UserService()
    # print("toke------",token_details["user"])

    user_email=token_details['user']['email']
    user=await user_service.get_user_by_email(user_email,db)
    return user 


