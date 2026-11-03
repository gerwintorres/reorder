import uvicorn

from reorder.core.config import Settings


def main() -> None:
    """Start the API server with the host and port from the settings."""
    settings = Settings()
    uvicorn.run("reorder.api.main:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
