from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from reorder.db.engine import engine

# expire_on_commit=False: a saved object keeps its values, so reading them to
# build the response doesn't trigger another SELECT.
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Provide one session per request and close it when the request ends.

    Closing rolls back whatever wasn't committed and returns the connection to
    the pool, also when the request fails.
    """
    with SessionLocal() as session:
        yield session
