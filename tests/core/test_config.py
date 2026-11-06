from pathlib import Path

import pytest
from pydantic import ValidationError

from reorder.core.config import DatabaseSettings, Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Neither the developer's shell nor their .env may leak into these tests:
    # .env is looked up in the current directory, so run from an empty one.
    for name in (
        "PORT",
        "REORDER_PORT",
        "REORDER_HOST",
        "REORDER_DATABASE_URL",
        "POSTGRES_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


def test_defaults_listen_on_localhost_port_8000() -> None:
    settings = Settings()
    assert (settings.host, settings.port) == ("127.0.0.1", 8000)


def test_reads_port_set_by_the_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "9000")
    assert Settings().port == 9000


def test_reads_host_with_app_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REORDER_HOST", "0.0.0.0")
    assert Settings().host == "0.0.0.0"


def test_reads_values_from_env_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("PORT=8123\n")
    assert Settings().port == 8123


def test_ignores_variables_meant_for_other_tools_in_env_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("POSTGRES_PASSWORD=change-me\nPORT=8123\n")
    assert Settings().port == 8123


def test_environment_variable_wins_over_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text("PORT=8123\n")
    monkeypatch.setenv("PORT", "9000")
    assert Settings().port == 9000


@pytest.mark.parametrize("port", ["abc", "0", "70000"])
def test_rejects_invalid_port(port: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", port)
    with pytest.raises(ValidationError):
        Settings()


def test_app_settings_do_not_need_a_database_url() -> None:
    assert Settings().port == 8000


def test_database_url_is_required() -> None:
    with pytest.raises(ValidationError):
        DatabaseSettings()


def test_reads_database_url_with_app_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    url = "postgresql+psycopg://app:fake-password@db.internal:5432/app"
    monkeypatch.setenv("REORDER_DATABASE_URL", url)
    assert DatabaseSettings().database_url.get_secret_value() == url


def test_database_url_can_reuse_the_password_in_env_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "POSTGRES_PASSWORD=change-me\n"
        "REORDER_DATABASE_URL=postgresql+psycopg://app:${POSTGRES_PASSWORD}@db/app\n"
    )
    assert DatabaseSettings().database_url.get_secret_value() == (
        "postgresql+psycopg://app:change-me@db/app"
    )


def test_app_settings_ignore_the_database_url_in_env_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("REORDER_DATABASE_URL=postgresql+psycopg://db/app\n")
    assert Settings().host == "127.0.0.1"


def test_database_password_stays_out_of_the_settings_repr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "REORDER_DATABASE_URL", "postgresql+psycopg://app:fake-password@db.internal/app"
    )
    assert "fake-password" not in repr(DatabaseSettings())
