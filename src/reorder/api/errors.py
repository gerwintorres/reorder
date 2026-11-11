from collections.abc import Mapping
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from reorder.schemas.errors import ErrorItem, ErrorsOut


class ApiError(Exception):
    """An error reported to the client in the API error format."""

    def __init__(self, status_code: int, field: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.field = field
        self.message = message


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    """Return an ApiError as {"errors": [{"field", "message"}]}."""
    errors = ErrorsOut(errors=[ErrorItem(field=exc.field, message=exc.message)])
    return JSONResponse(status_code=exc.status_code, content=errors.model_dump())


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return request validation errors as {"errors": [{"field", "message"}]}."""
    errors = ErrorsOut(
        errors=[
            ErrorItem(field=_field_name(error), message=error["msg"])
            for error in exc.errors()
        ]
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=errors.model_dump()
    )


def _field_name(error: Mapping[str, Any]) -> str:
    # loc starts with where the value came from: "body", "query" or "path".
    # For malformed JSON the rest is a character position, not a field.
    source, *path = error["loc"]
    if error["type"] == "json_invalid" or not path:
        return str(source)
    return ".".join(str(part) for part in path)
