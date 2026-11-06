from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, read from environment variables and an optional .env.

    App settings use the REORDER_ prefix. PORT is read without it, because
    hosting platforms set that name. Other variables in .env belong to other
    tools, such as Docker Compose, and are ignored.
    """

    model_config = SettingsConfigDict(
        env_prefix="REORDER_", env_file=".env", extra="ignore"
    )

    host: str = "127.0.0.1"
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("PORT", "REORDER_PORT"),
    )
