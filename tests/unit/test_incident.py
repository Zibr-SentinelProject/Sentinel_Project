"""Unit tests for the Incident model: its state rules."""
import uuid

import pytest

from app.models.incident import Incident


def make_incident():
    return Incident(uuid.uuid4(), "Phishing", "Correo sospechoso", Incident.HIGH)


def test_new_incident_is_open_and_has_no_analyst():
    incident = make_incident()

    assert incident.state == Incident.OPEN
    assert incident.analyst_id is None


def test_assign_sets_the_analyst():
    incident = make_incident()
    analyst = uuid.uuid4()

    incident.assign(analyst)

    assert incident.analyst_id == analyst


def test_creator_cannot_be_assigned_to_their_own_incident():
    incident = make_incident()

    with pytest.raises(ValueError):
        incident.assign(incident.user_id)


def test_close_sets_state_and_close_date():
    incident = make_incident()

    incident.close()

    assert incident.is_closed()
    assert incident.close_date is not None
