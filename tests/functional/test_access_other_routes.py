"""Functional tests, section 6.2.5: access tests on the other routes.

The test of section 6.1 (an employee opening the incident of someone else) is repeated on every
route that receives an ID or is restricted by role. All of them must be denied.
"""
from io import BytesIO

import pytest

from app.models.user import Employee

ANA = "ana@example.com"
EVA = "eva@example.com"

NEW_ACCOUNT = {"name": "Luis", "email": "luis@example.com", "password": "secret123"}


@pytest.fixture
def incident_of_ana(client, login, incidents):
    """An incident (with an attachment) created by Employee A, with nobody logged in afterwards."""
    login(ANA)
    client.post("/incidents/new", content_type="multipart/form-data",
                data={"title": "Phishing", "description": "Correo sospechoso", "severity": "3",
                      "file": (BytesIO(b"datos"), "informe.pdf")})
    client.post("/logout")
    return incidents.incidents[-1]


# Employee B, with the ID of an incident of Employee A

@pytest.mark.parametrize("method, path, data", [
    ("get", "/incidents/{id}/attachment", None),
    ("post", "/incidents/{id}/comments", {"content": "Comentario intruso"}),
    ("post", "/incidents/{id}/assign", {"analyst_id": "{eva_id}"}),
    ("post", "/incidents/{id}/close", None),
], ids=["attachment", "comments", "assign", "close"])
def test_employee_b_gets_404_on_the_incident_routes_of_employee_a(
        client, login, users, incident_of_ana, method, path, data):
    login(EVA)
    eva = users.get_by_email(EVA)
    url = path.format(id=incident_of_ana.id)
    data = {key: value.format(eva_id=eva.id) for key, value in data.items()} if data else None

    response = getattr(client, method)(url, data=data)

    assert response.status_code == 404


def test_the_denied_requests_of_employee_b_change_nothing(client, login, users, incident_of_ana):
    login(EVA)
    eva = users.get_by_email(EVA)
    client.post(f"/incidents/{incident_of_ana.id}/comments", data={"content": "Comentario intruso"})
    client.post(f"/incidents/{incident_of_ana.id}/assign", data={"analyst_id": str(eva.id)})
    client.post(f"/incidents/{incident_of_ana.id}/close")
    client.post("/logout")

    login(ANA)
    detail = client.get(f"/incidents/{incident_of_ana.id}")

    assert "Comentario intruso" not in detail.text
    assert incident_of_ana.analyst_id is None
    assert not incident_of_ana.is_closed()


# Employee (no admin role)

def test_employee_gets_403_on_the_users_list(client, login):
    login(ANA)

    assert client.get("/users").status_code == 403


def test_employee_gets_403_changing_a_role(client, login, users):
    login(ANA)
    eva = users.get_by_email(EVA)

    response = client.post(f"/users/{eva.id}/role", data={"role": "ADMIN"})

    assert response.status_code == 403
    assert isinstance(users.get_by_email(EVA), Employee)


# Tampering

def test_register_ignores_an_extra_role_field(client, users):
    response = client.post("/register", data={**NEW_ACCOUNT, "role": "ADMIN"})

    assert response.status_code == 302
    created = users.get_by_email(NEW_ACCOUNT["email"])
    assert type(created) is Employee
    assert created.get_role() == "EMPLOYEE"
