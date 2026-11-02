from collections.abc import Mapping
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from reorder.schemas.errors import ErrorItem, ErrorsOut


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
