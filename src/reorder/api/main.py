from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the service is up."""
    return {"status": "ok"}
