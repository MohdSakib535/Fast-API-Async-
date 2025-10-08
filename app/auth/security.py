from datetime import datetime, timedelta, timezone
from jose import JWTError,jwt
from .schemas import TokenData
from fastapi import HTTPException,status
from fastapi.security import OAuth2PasswordBearer,HTTPBearer,HTTPAuthorizationCredentials
from ..Database.session import get_db
from fastapi import Depends,HTTPException,status
from sqlalchemy import select
from .models import User
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from ..config.errors import *

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 310000



# note
"""
expires_delta: timedelta | None = <optional parameter>
if timedelta is not provided, the default value is None

"""



import uuid
import logging

def create_access_token2(user_data: dict, expiry: timedelta = None, refresh: bool = False):
    payload = {}

    payload["user"] = user_data
    payload["exp"] = datetime.now(timezone.utc) + (
        expiry if expiry is not None else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["jti"] = str(uuid.uuid4())

    payload["refresh"] = refresh

    token = jwt.encode(
        payload, SECRET_KEY, algorithm=ALGORITHM
    )

    return token



def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )

        return token_data

    except JWTError as e:
        logging.exception(e)
        return None

        


class TokenBearer(HTTPBearer):
    def __init__(self, *, bearerFormat = None, scheme_name = None, description = None, auto_error = True):
        super().__init__(bearerFormat=bearerFormat, scheme_name=scheme_name, description=description, auto_error=auto_error)


    async def __call__(self, request:Request):
        credentials: HTTPAuthorizationCredentials=  await super().__call__(request)
        # print("cred-------",credentials)
        if credentials:
            if credentials.scheme!="Bearer":
              raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            
        token=credentials.credentials
        

        token_data=decode_token(token)
        # print("token_data========",token_data)
            
        if not token_data:
            raise InvalidToken()
            # raise HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN,
            #     detail="Invalid or expired token"
            # )
        

        from ..Database.redis import token_in_blocklist

        if await token_in_blocklist(token_data['jti']):
            raise RevokedToken()
            # raise HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN,
            #     detail={
            #         "error":"this token is Invalid or expire",
            #         "Resolution":"please get new token"

            #     }
            # )


        
        self.verify_token_data(token_data)
        
       

        
        # print(credentials.scheme)
        # print(credentials.credentials)
        return token_data
    
    def token_valid(self,token:str)->bool:
        token_data=decode_token(token)
        return True if token_data else False
    

    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")



class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data['refresh']:
            raise AccessTokenRequired()
            # raise HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN,
            #     detail="Please provide a access token"
            # )
        

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data['refresh']:
            raise RefreshTokenRequired()
            # raise HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN,
            #     detail="Please provide a refresh token"
            # )
        