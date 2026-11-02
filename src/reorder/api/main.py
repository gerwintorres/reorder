from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from reorder.api.errors import validation_error_handler
from reorder.api.routers import estimate

app = FastAPI(
    exception_handlers={RequestValidationError: validation_error_handler},
)
app.include_router(estimate.router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the service is up."""
    return {"status": "ok"}
