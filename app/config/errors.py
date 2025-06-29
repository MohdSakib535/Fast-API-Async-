from typing import Any, Callable
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status,Header,HTTPException
from sqlalchemy.exc import SQLAlchemyError
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import traceback




class BooklyException(Exception):
    """This is the base class for all bookly errors"""

    pass


class InvalidToken(BooklyException):
    """User has provided an invalid or expired token"""

    pass


class RevokedToken(BooklyException):
    """User has provided a token that has been revoked"""

    pass


class AccessTokenRequired(BooklyException):
    """User has provided a refresh token when an access token is needed"""

    pass


class RefreshTokenRequired(BooklyException):
    """User has provided an access token when a refresh token is needed"""

    pass


class UserAlreadyExists(BooklyException):
    """User has provided an email for a user who exists during sign up."""

    pass


class InvalidCredentials(BooklyException):
    """User has provided wrong email or password during log in."""

    pass


class InsufficientPermission(BooklyException):
    """User does not have the neccessary permissions to perform an action."""

    pass


class BookNotFound(BooklyException):
    """Book Not found"""

    pass








def create_exception_handler(status_code: int, initial_detail: Any) -> Callable[[Request, Exception], JSONResponse]:

    async def exception_handler(request: Request, exc: BooklyException):

        return JSONResponse(content=initial_detail, status_code=status_code)

    return exception_handler




def register_all_errors(app: FastAPI):
    app.add_exception_handler(
        InvalidCredentials,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message":"Invalid credentials",
                "error_code":"auth_login"
            }
        )
    )


    app.add_exception_handler(
        UserAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message":"User with this email already Exist",
                "error_code":"auth_create_user"
            }
        )
    )


    app.add_exception_handler(
        InvalidToken,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message":"status.HTTP_403_FORBIDDEN",
                "error_code":"auth_token"
            }
        )
    )


    # Global exception handler for validation errors
    """
    Generally this error arise when when name mistake as per model is not define in pydantic 
    eg in book modes we have title but in pydantic if we mention titleq by mistake in this scenerio it come in thus exception handler
    
    """
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Input validation failed",
                "details": exc.errors(),
                "body": exc.body
            }
        )

    # Global exception handler for Pydantic validation errors(Used when you manually validate data using Pydantic models)
    @app.exception_handler(ValidationError)   
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Data validation failed",
                "details": exc.errors()
            }
        )

    # Global exception handler for HTTP exceptions
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )

    # Global exception handler for all other exceptions
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "type": type(exc).__name__
            }
        )




