from __future__ import annotations

import logging
import time
from typing import Awaitable, Callable

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("app.middleware")


async def _logging_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except SQLAlchemyError as exc:
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


def setup_middlewares(app: FastAPI) -> None:
    app.middleware("http")(_logging_middleware)
