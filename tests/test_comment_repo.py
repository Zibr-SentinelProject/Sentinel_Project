"""Pruebas unitarias de CommentRepository.

La conexión a la base se sustituye por un mock, así que no hace falta
MariaDB ni el archivo .env para ejecutarlas.
"""
import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pymysql
import pytest

from app.models.comment import Comment
from app.repositories.comment_repo import CommentRepository


@pytest.fixture
def cursor():
    return MagicMock()


@pytest.fixture
def connection(cursor):
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn


@pytest.fixture
def repo(connection):
    return CommentRepository(connection)


def test_create_executes_insert_and_commits(repo, connection, cursor):
    author = uuid.uuid4()
    incident = uuid.uuid4()
    new = Comment("Un comentario", author, incident)

    result = repo.create(new)

    query, params = cursor.execute.call_args.args
    assert query.startswith("INSERT INTO comments")
    assert params == (new.id, "Un comentario", author, incident, new.timestamp)
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    assert result is new


def test_create_rolls_back_and_reraises_on_db_error(repo, connection, cursor):
    cursor.execute.side_effect = pymysql.MySQLError("fallo simulado")
    new = Comment("Otro", uuid.uuid4(), uuid.uuid4())

    with pytest.raises(pymysql.MySQLError):
        repo.create(new)

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_get_by_id_returns_comment_from_row(repo, cursor):
    comment_id = uuid.uuid4()
    author = uuid.uuid4()
    incident = uuid.uuid4()
    timestamp = datetime(2026, 10, 22, 12, 0, 0)
    cursor.fetchone.return_value = {
        "id": str(comment_id),
        "content": "Hola",
        "author_id": str(author),
        "incident_id": str(incident),
        "timestamp": timestamp,
    }

    found = repo.get_by_id(comment_id)

    assert found.id == comment_id
    assert found.content == "Hola"
    assert found.author_id == author
    assert found.incident_id == incident
    assert found.timestamp == timestamp
    assert cursor.execute.call_args.args[1] == (comment_id,)


def test_get_by_id_returns_none_when_no_row(repo, cursor):
    cursor.fetchone.return_value = None

    assert repo.get_by_id(uuid.uuid4()) is None


def test_get_all_by_incident_maps_all_rows(repo, cursor):
    incident = uuid.uuid4()
    rows = [
        {
            "id": str(uuid.uuid4()),
            "content": f"Comentario {i}",
            "author_id": str(uuid.uuid4()),
            "incident_id": str(incident),
            "timestamp": datetime(2026, 10, 22, 12, i, 0),
        }
        for i in range(2)
    ]
    cursor.fetchall.return_value = rows

    result = repo.get_all_by_incident(incident)

    assert [c.content for c in result] == ["Comentario 0", "Comentario 1"]
    assert all(c.incident_id == incident for c in result)
    assert cursor.execute.call_args.args[1] == (incident,)


def test_get_all_by_incident_returns_empty_list(repo, cursor):
    cursor.fetchall.return_value = []

    assert repo.get_all_by_incident(uuid.uuid4()) == []


def test_comment_with_blank_content_is_rejected():
    with pytest.raises(ValueError):
        Comment("   ", uuid.uuid4(), uuid.uuid4())
