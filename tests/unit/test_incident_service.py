"""Unit tests for IncidentService: who sees what, who closes, and the ticket + attachment creation.

The repository is replaced by a mock, so no database is needed.
"""
import os
from unittest.mock import MagicMock

import pytest

from app.models.incident import Incident
from app.models.user import Analyst, Employee
from app.services.incident_service import IncidentService


@pytest.fixture
def repo():
    repo = MagicMock()
    repo.create.side_effect = lambda incident: incident
    return repo


@pytest.fixture
def service(repo):
    return IncidentService(repo)


@pytest.fixture
def ana():
    return Employee("Ana", "ana@example.com", "secret")


@pytest.fixture
def eva():
    return Employee("Eva", "eva@example.com", "secret")


@pytest.fixture
def analyst():
    return Analyst("Marta", "marta@example.com", "secret")


def test_employee_only_sees_their_own_incidents(service, repo, ana, eva):
    mine = Incident(ana.id, "mio", "d", 1)
    other = Incident(eva.id, "ajeno", "d", 1)
    repo.get_all.return_value = [mine, other]

    assert service.list_incidents(ana) == [mine]


def test_analyst_sees_every_incident(service, repo, ana, eva, analyst):
    repo.get_all.return_value = [Incident(ana.id, "a", "d", 1), Incident(eva.id, "b", "d", 1)]

    assert len(service.list_incidents(analyst)) == 2


def test_employee_cannot_open_an_incident_of_someone_else(service, repo, ana, eva):
    other = Incident(eva.id, "ajeno", "d", 1)
    repo.get_by_id.return_value = other

    with pytest.raises(PermissionError):
        service.get_incident(ana, other.id)


def test_only_the_assigned_analyst_can_close(service, repo, ana, analyst):
    incident = Incident(ana.id, "t", "d", 1)
    repo.get_by_id.return_value = incident
    other_analyst = Analyst("Luis", "luis@example.com", "secret")
    incident.assign(analyst.id)

    with pytest.raises(PermissionError):
        service.close_incident(other_analyst, incident.id)

    service.close_incident(analyst, incident.id)
    assert incident.is_closed()


def test_create_incident_with_file_saves_the_attachment_together_with_the_ticket(service, ana):
    incident = service.create_incident(ana, "t", "d", 1, None, "foto.png", "image/png", b"datos")

    assert incident.attachment.filename == "foto.png"
    with open(incident.attachment.path, "rb") as file:
        assert file.read() == b"datos"


def test_create_incident_removes_the_file_if_the_ticket_is_not_saved(service, repo, ana):
    repo.create.side_effect = RuntimeError("db caída")

    with pytest.raises(RuntimeError):
        service.create_incident(ana, "t", "d", 1, None, "foto.png", "image/png", b"x")

    assert os.listdir("attachments") == []
