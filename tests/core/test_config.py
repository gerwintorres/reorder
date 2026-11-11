from pathlib import Path

import pytest
from pydantic import ValidationError

from reorder.core.config import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Neither the developer's shell nor their .env may leak into these tests:
    # .env is looked up in the current directory, so run from an empty one.
    for name in ("PORT", "REORDER_PORT", "REORDER_HOST"):
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
