"""Unit tests for authorize(): every action, for every role, on every kind of incident.

No database and no Flask: authorize() only needs a user and, for incident actions, an incident.
"""
from uuid import UUID

import pytest

from app.models.incident import Incident
from app.models.user import Admin, Analyst, Employee
from app.services.authorization import (
    ASSIGN_INCIDENT,
    AccessDeniedError,
    BE_ASSIGNEE,
    CLOSE_INCIDENT,
    COMMENT_INCIDENT,
    DOWNLOAD_ATTACHMENT,
    LIST_ALL_INCIDENTS,
    LIST_INCIDENTS,
    MANAGE_USERS,
    VIEW_INCIDENT,
    authorize,
    require,
)

INCIDENT_ACTIONS = [VIEW_INCIDENT, DOWNLOAD_ATTACHMENT, COMMENT_INCIDENT, ASSIGN_INCIDENT, CLOSE_INCIDENT]
ALL_ACTIONS = INCIDENT_ACTIONS + [LIST_INCIDENTS, LIST_ALL_INCIDENTS, BE_ASSIGNEE, MANAGE_USERS]

# (who, incident) -> what is allowed, in the order of INCIDENT_ACTIONS:
#                            view   download comment assign  close
# "free" has no analyst; "taken" is assigned to "analyst".
# TODO: Admin.handle_incidents() is still undecided; if the owner changes it, update the admin rows.
MATRIX = {
    ("creator", "free"):          (True,  True,  True,  False, False),
    ("creator", "taken"):         (True,  True,  True,  False, False),
    ("other", "free"):            (False, False, False, False, False),
    ("other", "taken"):           (False, False, False, False, False),
    ("analyst", "free"):          (True,  True,  False, True,  False),
    ("analyst", "taken"):         (True,  True,  True,  True,  True),
    ("other_analyst", "free"):    (True,  True,  False, True,  False),
    ("other_analyst", "taken"):   (True,  True,  False, False, False),
    ("admin", "free"):            (True,  True,  False, False, False),
    ("admin", "taken"):           (True,  True,  False, False, False),
}


@pytest.fixture
def people():
    return {
        "creator": Employee("Ana", "ana@example.com", "x"),
        "other": Employee("Eva", "eva@example.com", "x"),
        "analyst": Analyst("Marta", "marta@example.com", "x"),
        "other_analyst": Analyst("Luis", "luis@example.com", "x"),
        "admin": Admin("Root", "root@example.com", "x"),
    }


@pytest.fixture
def incidents(people):
    taken = Incident(people["creator"].id, "t", "d", 1, analyst_id=people["analyst"].id)
    return {"free": Incident(people["creator"].id, "t", "d", 1), "taken": taken}


@pytest.mark.parametrize("who, kind", MATRIX)
def test_incident_actions_for_every_role(people, incidents, who, kind):
    for action, allowed in zip(INCIDENT_ACTIONS, MATRIX[(who, kind)]):
        # "is" and not "==": authorize must return a real bool, never None or another truthy value.
        assert authorize(people[who], action, incidents[kind]) is allowed, action


@pytest.mark.parametrize("who, list_all, be_assignee, manage_users", [
    ("creator", False, False, False),
    ("analyst", True, True, False),
    ("admin", True, False, True),
])
def test_actions_that_are_not_about_one_incident(people, who, list_all, be_assignee, manage_users):
    user = people[who]

    assert authorize(user, LIST_INCIDENTS) is True
    assert authorize(user, LIST_ALL_INCIDENTS) is list_all
    assert authorize(user, BE_ASSIGNEE) is be_assignee
    assert authorize(user, MANAGE_USERS) is manage_users


def test_an_employee_cannot_receive_an_assignment(people):
    assert authorize(people["creator"], BE_ASSIGNEE) is False


@pytest.mark.parametrize("action", ALL_ACTIONS)
def test_nobody_logged_in_is_denied_everything(incidents, action):
    assert authorize(None, action, incidents["taken"]) is False


def test_an_unknown_action_is_denied_even_to_an_admin(people, incidents):
    assert authorize(people["admin"], "delete_everything", incidents["taken"]) is False
    assert authorize(people["admin"], "delete_everything") is False


@pytest.mark.parametrize("action", INCIDENT_ACTIONS)
def test_an_incident_action_without_an_incident_is_denied(people, action):
    assert authorize(people["analyst"], action) is False


@pytest.mark.parametrize("action", [COMMENT_INCIDENT, CLOSE_INCIDENT])
def test_an_assigned_analyst_who_became_employee_loses_the_access(people, incidents, action):
    # Changing the role makes the repository rebuild the same id as an Employee.
    analyst = people["analyst"]
    demoted = Employee("Marta", "marta@example.com", "x", id=analyst.id)

    assert authorize(analyst, action, incidents["taken"]) is True
    assert authorize(demoted, action, incidents["taken"]) is False


def test_ids_read_from_the_database_are_compared_as_uuid(people):
    # The repositories build every id with UUID(str(row[...])), so creator and user are the same type.
    creator = people["creator"]
    from_db = Incident(UUID(str(creator.id)), "t", "d", 1)

    assert authorize(creator, VIEW_INCIDENT, from_db) is True


def test_ids_of_different_types_fail_closed(people):
    # A str id never equals a UUID: the creator would be denied (safe, but it would be a bug to chase).
    creator = people["creator"]
    wrong_type = Incident(str(creator.id), "t", "d", 1)

    assert authorize(creator, VIEW_INCIDENT, wrong_type) is False


def test_require_does_nothing_when_it_is_allowed(people, incidents):
    require(people["creator"], VIEW_INCIDENT, incidents["free"])
    require(people["admin"], MANAGE_USERS)


def test_require_answers_404_when_the_action_is_about_an_incident(people, incidents):
    with pytest.raises(AccessDeniedError) as error:
        require(people["other"], VIEW_INCIDENT, incidents["free"])

    assert error.value.status == 404


def test_require_answers_403_when_there_is_no_object_only_the_role(people):
    with pytest.raises(AccessDeniedError) as error:
        require(people["analyst"], MANAGE_USERS)

    assert error.value.status == 403


def test_access_denied_is_not_a_permission_error():
    # If it were, the old handler (flash + redirect to the Referer) would catch it.
    assert not issubclass(AccessDeniedError, PermissionError)
