"""Pruebas unitarias de IncidentRepository.

La conexión a la base se sustituye por un mock, así que no hace falta
MariaDB ni el archivo .env para ejecutarlas.
"""
import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pymysql
import pytest

from app.models.incident import Incident
from app.repositories.incident_repo import IncidentRepository


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
    return IncidentRepository(connection)


def make_row(incident_id, user_id, analyst_id=None, state_id=1):
    """Fila tal como la devuelve la consulta SELECT del repositorio."""
    return {
        "id": str(incident_id),
        "user_id": str(user_id),
        "analyst_id": str(analyst_id) if analyst_id else None,
        "title": "Phishing",
        "description": "Correo sospechoso",
        "severity_id": 3,
        "severity_name": "HIGH",
        "state_id": state_id,
        "state_name": "OPEN",
        "open_date": datetime(2026, 10, 1, 9, 0, 0),
        "close_date": None,
        "user_name": "Ana",
        "user_email": "ana@example.com",
        "analyst_name": None,
        "analyst_email": None,
    }


def test_create_executes_insert_with_schema_columns_and_commits(repo, connection, cursor):
    user = uuid.uuid4()
    new = Incident(user, "Phishing", "Correo sospechoso", 3)

    result = repo.create(new)

    query, params = cursor.execute.call_args.args
    assert query.startswith("INSERT INTO incident")
    assert "severity_id" in query and "state_id" in query
    assert params[0] == new.id
    assert params[4] == 3
    assert params[5] == Incident.OPEN
    assert params[8] is None
    connection.commit.assert_called_once()
    assert result is new


def test_create_rolls_back_and_reraises_on_db_error(repo, connection, cursor):
    cursor.execute.side_effect = pymysql.MySQLError("fallo simulado")

    with pytest.raises(pymysql.MySQLError):
        repo.create(Incident(uuid.uuid4(), "t", "d", 1))

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_get_by_id_returns_incident_from_row(repo, cursor):
    incident_id = uuid.uuid4()
    user = uuid.uuid4()
    analyst = uuid.uuid4()
    cursor.fetchone.return_value = make_row(incident_id, user, analyst_id=analyst, state_id=2)

    incident = repo.get_by_id(incident_id)

    assert isinstance(incident, Incident)
    assert incident.id == incident_id
    assert incident.user_id == user
    assert incident.analyst_id == analyst
    assert incident.severity == 3
    assert incident.state == 2


def test_get_by_id_accepts_unassigned_incident(repo, cursor):
    incident_id = uuid.uuid4()
    cursor.fetchone.return_value = make_row(incident_id, uuid.uuid4(), analyst_id=None)

    assert repo.get_by_id(incident_id).analyst_id is None


def test_get_by_id_returns_none_when_missing(repo, cursor):
    cursor.fetchone.return_value = None

    assert repo.get_by_id(uuid.uuid4()) is None


def test_get_all_returns_every_row_as_incident(repo, cursor):
    cursor.fetchall.return_value = [
        make_row(uuid.uuid4(), uuid.uuid4()),
        make_row(uuid.uuid4(), uuid.uuid4()),
    ]

    incidents = repo.get_all()

    assert len(incidents) == 2
    assert all(isinstance(i, Incident) for i in incidents)


def test_get_by_user_filters_by_user_id(repo, cursor):
    user = uuid.uuid4()
    cursor.fetchall.return_value = [make_row(uuid.uuid4(), user)]

    incidents = repo.get_by_user(user)

    query, params = cursor.execute.call_args.args
    assert "WHERE i.user_id = %s" in query
    assert params == (user,)
    assert len(incidents) == 1
    assert incidents[0].user_id == user


def test_get_by_user_returns_empty_list_when_none(repo, cursor):
    cursor.fetchall.return_value = []

    assert repo.get_by_user(uuid.uuid4()) == []


def test_update_writes_state_analyst_and_close_date_then_commits(repo, connection, cursor):
    incident = Incident(uuid.uuid4(), "t", "d", 2)
    incident.close()

    result = repo.update(incident.id, incident)

    query, params = cursor.execute.call_args.args
    assert "severity_id = %s" in query and "state_id = %s" in query and "close_date = %s" in query
    assert params[1] == Incident.CLOSED
    assert params[3] == incident.close_date
    assert params[4] == incident.id
    connection.commit.assert_called_once()
    assert result is incident


def test_delete_returns_true_when_row_removed(repo, cursor):
    cursor.rowcount = 1

    assert repo.delete(uuid.uuid4()) is True


def test_delete_returns_false_when_nothing_removed(repo, cursor):
    cursor.rowcount = 0

    assert repo.delete(uuid.uuid4()) is False
