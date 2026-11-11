from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Other variables in .env belong to other tools, such as Docker Compose.
ENV_CONFIG = SettingsConfigDict(env_prefix="REORDER_", env_file=".env", extra="ignore")


class Settings(BaseSettings):
    """Runtime settings, read from environment variables and an optional .env.

    App settings use the REORDER_ prefix. PORT is read without it, because
    hosting platforms set that name.
    """

    model_config = ENV_CONFIG

    host: str = "127.0.0.1"
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("PORT", "REORDER_PORT"),
    )


class DatabaseSettings(BaseSettings):
    """Database settings, kept apart so the API can start without a database.

    The URL holds a password, so it has no default and only comes from the
    environment.
    """

    model_config = ENV_CONFIG

    database_url: SecretStr
