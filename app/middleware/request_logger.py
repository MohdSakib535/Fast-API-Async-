from __future__ import annotations

import logging
import time
from typing import Awaitable, Callable

from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


logger = logging.getLogger("app.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each request/response cycle and adds processing time to the headers."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except SQLAlchemyError:
            logger.exception("Database error during %s %s", request.method, request.url.path)
            raise
        except Exception:
            logger.exception("Unhandled error during %s %s", request.method, request.url.path)
            raise

        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}s"
        logger.info(
            "%s %s completed with status %s in %.4fs",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response
