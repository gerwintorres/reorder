from fastapi import FastAPI

from reorder.api.routers import estimate

app = FastAPI()
app.include_router(estimate.router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the service is up."""
    return {"status": "ok"}
