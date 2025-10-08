from __future__ import annotations

import json
from typing import Awaitable, Callable

from fastapi import status
from fastapi.exceptions import RequestValidationError
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
            response = await call_next(request)
        except RequestValidationError as exc:
            return self._build_validation_response(exc.errors())

        return self._transform_validation_response(response)

    @staticmethod
    def _build_validation_response(errors: list[dict[str, object]] | None) -> JSONResponse:
        return JSONResponse(
            {"message": "Schema validation failed", "errors": errors or []},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def _transform_validation_response(self, response: Response) -> Response:
        if response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY:
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return response

        body_content = getattr(response, "body", b"")
        if not body_content:
            return response

        try:
            if isinstance(body_content, (bytes, bytearray, memoryview)):
                body_text = bytes(body_content).decode("utf-8")
            elif isinstance(body_content, str):
                body_text = body_content
            else:
                body_text = str(body_content)
        except UnicodeDecodeError:
            return response

        try:
            payload = json.loads(body_text)
        except (json.JSONDecodeError, TypeError):
            return response

        errors = payload.get("detail")
        if not isinstance(errors, list):
            return response

        return self._build_validation_response(errors)
