"""Unit tests for IncidentService: who sees what, who closes, and the ticket + attachment creation.

The repository is replaced by a mock, so no database is needed.
"""
import os
from unittest.mock import MagicMock

import pytest

from app.models.attachment import Attachment
from app.models.incident import Incident
from app.models.user import Admin, Analyst, Employee
from app.services.authorization import AccessDeniedError
from app.services.incident_service import IncidentService


@pytest.fixture
def repo():
    repo = MagicMock()
    repo.create.side_effect = lambda incident: incident
    return repo


@pytest.fixture
def user_service():
    return MagicMock()


@pytest.fixture
def service(repo, user_service):
    return IncidentService(repo, user_service)


@pytest.fixture
def ana():
    return Employee("Ana", "ana@example.com", "secret")


@pytest.fixture
def eva():
    return Employee("Eva", "eva@example.com", "secret")


@pytest.fixture
def analyst():
    return Analyst("Marta", "marta@example.com", "secret")


def test_employee_only_loads_their_own_incidents_from_the_query(service, repo, ana):
    mine = Incident(ana.id, "mio", "d", 1)
    repo.get_by_user.return_value = [mine]

    assert service.list_incidents(ana) == [mine]
    # The other people's incidents are never loaded, not even to be filtered out afterwards.
    repo.get_by_user.assert_called_once_with(ana.id)
    repo.get_all.assert_not_called()


@pytest.mark.parametrize("who", ["analyst", "admin"])
def test_who_can_see_everything_gets_every_incident(service, repo, ana, eva, analyst, who):
    person = analyst if who == "analyst" else Admin("Root", "root@example.com", "secret")
    repo.get_all.return_value = [Incident(ana.id, "a", "d", 1), Incident(eva.id, "b", "d", 1)]

    assert len(service.list_incidents(person)) == 2
    repo.get_by_user.assert_not_called()


def test_employee_cannot_open_an_incident_of_someone_else(service, repo, ana, eva):
    other = Incident(eva.id, "ajeno", "d", 1)
    repo.get_by_id.return_value = other

    with pytest.raises(AccessDeniedError) as error:
        service.get_incident(ana, other.id)

    assert error.value.status == 404


def test_a_missing_incident_raises_lookup_error(service, repo, ana):
    repo.get_by_id.return_value = None
    with pytest.raises(LookupError):
        service.get_incident(ana, "missing-id")


def test_only_the_assigned_analyst_can_close(service, repo, ana, analyst):
    incident = Incident(ana.id, "t", "d", 1)
    repo.get_by_id.return_value = incident
    other_analyst = Analyst("Luis", "luis@example.com", "secret")
    incident.assign(analyst.id)

    for person in (other_analyst, ana):
        with pytest.raises(AccessDeniedError):
            service.close_incident(person, incident.id)

    service.close_incident(analyst, incident.id)
    assert incident.is_closed()


def test_an_assigned_analyst_who_became_employee_cannot_close(service, repo, ana, analyst):
    incident = Incident(ana.id, "t", "d", 1, analyst_id=analyst.id)
    repo.get_by_id.return_value = incident
    demoted = Employee("Marta", "marta@example.com", "secret", id=analyst.id)

    with pytest.raises(AccessDeniedError):
        service.close_incident(demoted, incident.id)


def test_an_analyst_assigns_a_free_incident_to_another_analyst(service, repo, user_service, ana, analyst):
    incident = Incident(ana.id, "t", "d", 1)
    repo.get_by_id.return_value = incident
    luis = Analyst("Luis", "luis@example.com", "secret")
    user_service.get_user.return_value = luis

    service.assign_incident(analyst, incident.id, luis.id)

    assert incident.analyst_id == luis.id


def test_an_employee_cannot_assign(service, repo, ana, eva):
    repo.get_by_id.return_value = Incident(ana.id, "t", "d", 1)

    with pytest.raises(AccessDeniedError):
        service.assign_incident(eva, "any-id", ana.id)


def test_only_the_assigned_analyst_can_reassign_a_taken_incident(service, repo, ana, analyst):
    incident = Incident(ana.id, "t", "d", 1, analyst_id=analyst.id)
    repo.get_by_id.return_value = incident
    other_analyst = Analyst("Luis", "luis@example.com", "secret")

    with pytest.raises(AccessDeniedError):
        service.assign_incident(other_analyst, incident.id, other_analyst.id)


def test_an_incident_cannot_be_assigned_to_someone_who_does_not_handle_incidents(
        service, repo, user_service, ana, eva, analyst):
    incident = Incident(ana.id, "t", "d", 1)
    repo.get_by_id.return_value = incident
    user_service.get_user.return_value = eva  # an Employee sent as analyst_id by the browser

    with pytest.raises(ValueError):
        service.assign_incident(analyst, incident.id, eva.id)
    assert incident.analyst_id is None


def test_assigning_to_a_user_that_does_not_exist_raises_lookup_error(service, repo, user_service, ana, analyst):
    repo.get_by_id.return_value = Incident(ana.id, "t", "d", 1)
    user_service.get_user.side_effect = LookupError("User not found")

    with pytest.raises(LookupError):
        service.assign_incident(analyst, "any-id", "missing-user")


def test_create_incident_with_file_saves_the_attachment_together_with_the_ticket(service, ana):
    incident = service.create_incident(ana, "t", "d", 1, None, "foto.png", "image/png", b"datos")

    assert incident.attachment.filename == "foto.png"
    with open(incident.attachment.path, "rb") as file:
        assert file.read() == b"datos"


def test_create_incident_removes_the_file_if_the_ticket_is_not_saved(service, repo, ana):
    repo.create.side_effect = RuntimeError("db caída")

    with pytest.raises(RuntimeError):
        service.create_incident(ana, "t", "d", 1, None, "foto.png", "image/png", b"x")

    assert os.listdir(Attachment.folder()) == []
