from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """Returns a friendly message when payload validation fails."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            if exc.__class__.__name__ != "RequestValidationError":
                raise

            response_payload = {
                "message": "Schema validation failed",
                "errors": getattr(exc, "errors", lambda: [])(),
            }
            return JSONResponse(response_payload, status_code=status.HTTP_400_BAD_REQUEST)
