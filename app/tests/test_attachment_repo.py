"""Pruebas unitarias de AttachmentRepository y del modelo Attachment
"""
import uuid
from unittest.mock import MagicMock

import pymysql
import pytest

from app.models.attachement import Attachment
from app.repositories.attachment_repo import AttachmentRepository


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
    return AttachmentRepository(connection)


def make_row(incident_id, filename="foto.png"):
    return {
        "id": str(uuid.uuid4()),
        "incident_id": str(incident_id),
        "filename": filename,
        "filetype": "image/png",
        "filesize": 1024,
    }


def test_create_executes_insert_and_commits(repo, connection, cursor):
    incident = uuid.uuid4()
    new = Attachment(incident, "foto.png", "image/png", 1024)

    result = repo.create(new)

    query, params = cursor.execute.call_args.args
    assert query.startswith("INSERT INTO attachment")
    assert params == (new.id, incident, "foto.png", "image/png", 1024, "attachments/foto.png")
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    assert result is new


def test_create_rolls_back_and_reraises_on_db_error(repo, connection, cursor):
    cursor.execute.side_effect = pymysql.MySQLError("fallo simulado")
    new = Attachment(uuid.uuid4(), "doc.pdf", "application/pdf", 2048)

    with pytest.raises(pymysql.MySQLError):
        repo.create(new)

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_get_by_id_returns_attachment_from_row(repo, cursor):
    attachment_id = uuid.uuid4()
    incident = uuid.uuid4()
    row = make_row(incident)
    row["id"] = str(attachment_id)
    cursor.fetchone.return_value = row

    found = repo.get_by_id(attachment_id)

    assert found.id == attachment_id
    assert found.incident_id == incident
    assert found.filename == "foto.png"
    assert found.filetype == "image/png"
    assert found.filesize == 1024
    assert cursor.execute.call_args.args[1] == (attachment_id,)


def test_get_by_id_returns_none_when_no_row(repo, cursor):
    cursor.fetchone.return_value = None

    assert repo.get_by_id(uuid.uuid4()) is None


def test_get_all_by_incident_maps_all_rows(repo, cursor):
    incident = uuid.uuid4()
    cursor.fetchall.return_value = [make_row(incident, "a.png"), make_row(incident, "b.png")]

    result = repo.get_all_by_incident(incident)

    assert [a.filename for a in result] == ["a.png", "b.png"]
    assert all(a.incident_id == incident for a in result)
    assert cursor.execute.call_args.args[1] == (incident,)


def test_get_all_by_incident_returns_empty_list(repo, cursor):
    cursor.fetchall.return_value = []

    assert repo.get_all_by_incident(uuid.uuid4()) == []


def test_delete_returns_true_when_row_deleted(repo, connection, cursor):
    attachment_id = uuid.uuid4()
    cursor.rowcount = 1

    assert repo.delete(attachment_id) is True

    query, params = cursor.execute.call_args.args
    assert query.startswith("DELETE FROM attachment")
    assert params == (attachment_id,)
    connection.commit.assert_called_once()


def test_delete_returns_false_when_id_does_not_exist(repo, connection, cursor):
    cursor.rowcount = 0

    assert repo.delete(uuid.uuid4()) is False
    connection.commit.assert_called_once()


def test_delete_rolls_back_and_reraises_on_db_error(repo, connection, cursor):
    cursor.execute.side_effect = pymysql.MySQLError("fallo simulado")

    with pytest.raises(pymysql.MySQLError):
        repo.delete(uuid.uuid4())

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_update_is_not_supported(repo):
    with pytest.raises(NotImplementedError):
        repo.update(uuid.uuid4(), None)


@pytest.mark.parametrize("filetype, size, expected", [
    ("image/png", 1024, True),
    ("application/pdf", 5 * 1024 * 1024, True),
    ("application/zip", 1024, False),
    ("image/png", 5 * 1024 * 1024 + 1, False),
])
def test_attachment_is_valid(filetype, size, expected):
    attachment = Attachment(uuid.uuid4(), "archivo", filetype, size)

    assert attachment.is_valid() is expected
