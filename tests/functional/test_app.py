"""Functional tests: the main flows of the app, from the browser's point of view."""
from io import BytesIO

ANA = "ana@example.com"
EVA = "eva@example.com"
MARTA = "marta@example.com"


def create_incident(client, incidents, title="Phishing", severity="3", **extra):
    """Creates a ticket through the form and returns it."""
    data = {"title": title, "description": "Correo sospechoso", "severity": severity, **extra}
    client.post("/incidents/new", data=data, content_type="multipart/form-data")
    return incidents.incidents[-1]


def test_login_with_a_wrong_password_shows_an_error(client):
    response = client.post("/login", data={"email": ANA, "password": "mal"})

    assert response.status_code == 401
    assert "Invalid email or password" in response.text


def test_the_list_needs_a_login(client):
    response = client.get("/incidents")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_create_a_ticket_and_see_it_in_the_list_and_the_detail(client, login, incidents):
    login(ANA)

    incident = create_incident(client, incidents, source_url="http://ejemplo.com")

    assert "Phishing" in client.get("/incidents").text
    detail = client.get(f"/incidents/{incident.id}").text
    assert "Correo sospechoso" in detail
    assert "Titulo de la pagina" in detail


def test_the_attachment_is_saved_with_the_ticket_and_can_be_downloaded(client, login, incidents):
    login(ANA)

    incident = create_incident(client, incidents, file=(BytesIO(b"datos"), "informe.pdf"))

    assert "informe.pdf" in client.get(f"/incidents/{incident.id}").text
    assert client.get(f"/incidents/{incident.id}/attachment").data == b"datos"


def test_a_comment_appears_in_the_detail(client, login, incidents):
    login(ANA)
    incident = create_incident(client, incidents)

    client.post(f"/incidents/{incident.id}/comments", data={"content": "Gracias por avisar"})

    assert "Gracias por avisar" in client.get(f"/incidents/{incident.id}").text


def test_search_filters_the_list_by_title(client, login, incidents):
    login(ANA)
    create_incident(client, incidents, title="Phishing")
    create_incident(client, incidents, title="Ransomware")

    page = client.get("/incidents?title=phish").text

    assert "Phishing" in page
    assert "Ransomware" not in page


def test_the_severity_filter_is_remembered_in_a_cookie(client, login, incidents):
    login(ANA)
    create_incident(client, incidents, title="Leve", severity="1")
    create_incident(client, incidents, title="Critico", severity="4")

    client.get("/incidents?severity=4")
    page = client.get("/incidents").text

    assert "Critico" in page
    assert "Leve" not in page


def test_an_employee_cannot_open_the_ticket_of_someone_else(client, login, incidents):
    login(ANA)
    incident = create_incident(client, incidents)
    client.post("/logout")

    login(EVA)
    response = client.get(f"/incidents/{incident.id}", headers={"Referer": "https://evil.example/"})

    # Same 404 page as an incident that does not exist, and never a redirect.
    assert response.status_code == 404
    assert "Location" not in response.headers
    assert "Not found" in response.text


def test_an_analyst_assigns_and_closes_a_ticket(client, login, users, incidents):
    login(ANA)
    incident = create_incident(client, incidents)
    client.post("/logout")

    login(MARTA)
    marta = users.get_by_email(MARTA)
    client.post(f"/incidents/{incident.id}/assign", data={"analyst_id": str(marta.id)})
    client.post(f"/incidents/{incident.id}/close")

    assert incident.is_closed()
    assert "CLOSED" in client.get(f"/incidents/{incident.id}").text


def test_a_missing_incident_and_a_forbidden_one_look_exactly_the_same(client, login, incidents):
    from uuid import uuid4

    login(ANA)
    incident = create_incident(client, incidents)
    client.post("/logout")
    login(EVA)

    forbidden = client.get(f"/incidents/{incident.id}")
    missing = client.get(f"/incidents/{uuid4()}")

    assert (forbidden.status_code, forbidden.text) == (missing.status_code, missing.text)


def test_every_incident_route_answers_404_to_someone_who_may_not_use_it(client, login, incidents, users):
    login(ANA)
    incident = create_incident(client, incidents, file=(BytesIO(b"datos"), "informe.pdf"))
    client.post("/logout")
    login(EVA)
    eva = users.get_by_email(EVA)

    responses = [
        client.get(f"/incidents/{incident.id}/attachment"),
        client.post(f"/incidents/{incident.id}/comments", data={"content": "hola"}),
        client.post(f"/incidents/{incident.id}/assign", data={"analyst_id": str(eva.id)}),
        client.post(f"/incidents/{incident.id}/close"),
    ]

    assert [response.status_code for response in responses] == [404, 404, 404, 404]
    assert incident.analyst_id is None and not incident.is_closed()


def test_an_incident_cannot_be_assigned_to_an_employee_sent_by_the_browser(client, login, users, incidents):
    login(ANA)
    incident = create_incident(client, incidents)
    client.post("/logout")
    login(MARTA)
    eva = users.get_by_email(EVA)

    client.post(f"/incidents/{incident.id}/assign", data={"analyst_id": str(eva.id)})

    assert incident.analyst_id is None


def test_assign_with_a_missing_or_invalid_analyst_id_is_not_a_500(client, login, incidents):
    login(ANA)
    incident = create_incident(client, incidents)
    client.post("/logout")
    login(MARTA)

    no_field = client.post(f"/incidents/{incident.id}/assign", data={})
    not_a_uuid = client.post(f"/incidents/{incident.id}/assign", data={"analyst_id": "xyz"})

    assert no_field.status_code < 500 and not_a_uuid.status_code < 500
    assert incident.analyst_id is None


def test_only_the_buttons_the_user_can_use_are_shown(client, login, incidents, users):
    login(ANA)
    incident = create_incident(client, incidents)
    assert "Assign analyst" not in client.get(f"/incidents/{incident.id}").text
    client.post("/logout")

    login(MARTA)
    page = client.get(f"/incidents/{incident.id}").text
    assert "Assign analyst" in page
    assert "Close incident" not in page
