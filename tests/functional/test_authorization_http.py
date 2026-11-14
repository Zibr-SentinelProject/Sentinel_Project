"""Functional tests for requires_permission and the AccessDeniedError error page.

The routes are added to the test app only here, so nothing is left in the real app.
"""
from app.models.incident import Incident
from app.models.user import Admin
from app.routes.common import requires_permission
from app.services.authorization import MANAGE_USERS, VIEW_INCIDENT, require
from app.utils.security import hash_password

ANA = "ana@example.com"
EVA = "eva@example.com"
MARTA = "marta@example.com"


def add_routes(client, other_users_incident):
    """Two routes: one about no object (MANAGE_USERS) and one about the incident of someone else."""
    @requires_permission(MANAGE_USERS)
    def only_admins(user):
        return f"hello {user.name}"

    @requires_permission(VIEW_INCIDENT)
    def about_an_incident(user):
        return "unreachable"

    def about_the_incident_of_someone_else():
        from app.routes.common import current_user
        require(current_user(), VIEW_INCIDENT, other_users_incident)
        return "unreachable"

    app = client.application
    app.add_url_rule("/_test/admins", "only_admins", only_admins)
    app.add_url_rule("/_test/incident", "someone_elses", about_the_incident_of_someone_else)


def test_without_a_login_it_goes_to_the_login(client):
    add_routes(client, None)

    response = client.get("/_test/admins")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_a_logged_user_without_the_role_gets_a_403_page_and_no_redirect(client, login):
    add_routes(client, None)
    login(MARTA)

    # The Referer is attacker-controlled: it must not decide where the user goes.
    response = client.get("/_test/admins", headers={"Referer": "https://evil.example/"})

    assert response.status_code == 403
    assert "Forbidden" in response.text
    assert "Location" not in response.headers


def test_an_admin_gets_in_and_receives_the_user(client, login, users):
    add_routes(client, None)
    users.create(Admin("Root", "root@example.com", hash_password("secret123")))
    login("root@example.com")

    response = client.get("/_test/admins")

    assert response.status_code == 200
    assert response.text == "hello Root"


def test_an_incident_of_someone_else_gets_a_404_page(client, login, users):
    eva = users.get_by_email(EVA)
    add_routes(client, Incident(eva.id, "t", "d", 1))
    login(ANA)

    response = client.get("/_test/incident", headers={"Referer": "https://evil.example/"})

    assert response.status_code == 404
    assert "Not found" in response.text
    assert "Location" not in response.headers
