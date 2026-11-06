from sqlalchemy import create_engine

from reorder.core.config import DatabaseSettings

# pydantic fills database_url from the environment, which mypy can't see.
settings = DatabaseSettings()  # type: ignore[call-arg]

# No connection is opened here: the pool creates them on the first query.
# pool_pre_ping replaces connections the database closed while they sat idle.
engine = create_engine(settings.database_url.get_secret_value(), pool_pre_ping=True)
