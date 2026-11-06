from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from reorder.db.session import get_db


def open_session() -> tuple[Session, Generator[Session, None, None]]:
    # A Session connects on its first query, so none of these tests need a database.
    generator = get_db()
    session = next(generator)
    session.begin()
    return session, generator


def test_get_db_yields_a_session() -> None:
    session, _ = open_session()
    assert isinstance(session, Session)


def test_get_db_yields_a_new_session_on_each_call() -> None:
    first, _ = open_session()
    second, _ = open_session()
    assert first is not second


def test_get_db_closes_the_session_when_the_request_ends() -> None:
    session, generator = open_session()
    with pytest.raises(StopIteration):
        next(generator)
    assert not session.in_transaction()


def test_get_db_closes_the_session_when_the_request_fails() -> None:
    session, generator = open_session()
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError("request failed"))
    assert not session.in_transaction()
