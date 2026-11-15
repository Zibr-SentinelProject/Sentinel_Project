"""After a validation error (ValueError) the app goes back to the previous page, but only if it is its own page."""
import pytest

ROOT = "root@example.com"
INVALID_USER = {"name": "Luis", "email": "luis@example.com", "password": "secret123", "role": "SUPERUSER"}


def send_invalid_form(client, referer):
    """An admin sends a form that fails validation, with the given Referer header."""
    headers = {"Referer": referer} if referer is not None else {}
    return client.post("/users/new", data=INVALID_USER, headers=headers)


def test_it_goes_back_to_the_page_of_this_same_app(client, login):
    login(ROOT)

    response = send_invalid_form(client, "http://localhost/users/new?x=1")

    assert response.status_code == 302
    assert response.headers["Location"] == "/users/new?x=1"


def test_the_error_message_is_shown_on_the_page_it_goes_back_to(client, login):
    login(ROOT)

    send_invalid_form(client, "http://localhost/users/new")

    assert "Invalid role" in client.get("/users/new").text


@pytest.mark.parametrize("referer", [
    "https://evil.example/phishing",      # another site
    "http://localhost.evil.example/",     # looks like ours, it is not
    "http://localhost//evil.example",     # same host, but "//evil.example" leaves the site
    "http://localhost/\\evil.example",    # backslash trick
    "http://evil@localhost/x",            # user info before the host
    "not a url at all",
    "",
    None,
])
def test_any_other_referer_goes_to_the_incidents(client, login, referer):
    login(ROOT)

    response = send_invalid_form(client, referer)

    assert response.status_code == 302
    assert response.headers["Location"] == "/incidents"
