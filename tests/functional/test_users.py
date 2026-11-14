"""Functional tests for /users: only whoever manages the users (the admin) can use these routes."""
from uuid import uuid4

import pytest

from app.models.user import Admin, Analyst, Employee

ANA = "ana@example.com"
MARTA = "marta@example.com"
ROOT = "root@example.com"

NEW_USER = {"name": "Luis", "email": "luis@example.com", "password": "secret123", "role": "ANALYST"}


@pytest.mark.parametrize("who", [ANA, MARTA])
def test_employees_and_analysts_get_403_in_every_users_route(client, login, users, who):
    login(who)
    ana = users.get_by_email(ANA)

    responses = [
        client.get("/users"),
        client.get("/users/new"),
        client.post("/users/new", data=NEW_USER),
        client.post(f"/users/{ana.id}/role", data={"role": "ADMIN"}),
    ]

    assert [response.status_code for response in responses] == [403, 403, 403, 403]
    assert users.get_by_email("luis@example.com") is None
    assert isinstance(users.get_by_email(ANA), Employee)


def test_without_a_login_the_users_routes_go_to_the_login(client):
    response = client.get("/users")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_the_admin_sees_the_list_and_the_users_button(client, login):
    login(ROOT)

    assert "ana@example.com" in client.get("/users").text
    assert 'href="/users"' in client.get("/incidents").text


def test_an_analyst_does_not_see_the_users_button(client, login):
    login(MARTA)

    assert 'href="/users"' not in client.get("/incidents").text


def test_the_admin_creates_a_user_with_the_role_chosen(client, login, users):
    login(ROOT)

    client.post("/users/new", data=NEW_USER)

    assert isinstance(users.get_by_email("luis@example.com"), Analyst)


def test_creating_a_user_with_an_invalid_role_does_not_create_it(client, login, users):
    login(ROOT)

    client.post("/users/new", data={**NEW_USER, "role": "SUPERUSER"})

    assert users.get_by_email("luis@example.com") is None


def test_the_admin_changes_a_role(client, login, users):
    login(ROOT)
    ana = users.get_by_email(ANA)

    client.post(f"/users/{ana.id}/role", data={"role": "ANALYST"})

    assert isinstance(users.get_by_email(ANA), Analyst)


def test_the_admin_cannot_change_their_own_role(client, login, users):
    login(ROOT)
    root = users.get_by_email(ROOT)

    client.post(f"/users/{root.id}/role", data={"role": "EMPLOYEE"})

    assert isinstance(users.get_by_email(ROOT), Admin)


def test_changing_to_an_invalid_role_changes_nothing(client, login, users):
    login(ROOT)
    ana = users.get_by_email(ANA)

    client.post(f"/users/{ana.id}/role", data={"role": "SUPERUSER"})

    assert isinstance(users.get_by_email(ANA), Employee)


def test_changing_the_role_of_a_missing_user_is_a_404_page_not_a_500(client, login):
    login(ROOT)

    response = client.post(f"/users/{uuid4()}/role", data={"role": "ANALYST"},
                           headers={"Referer": "https://evil.example/"})

    assert response.status_code == 404
    assert "Not found" in response.text
    assert "Location" not in response.headers
