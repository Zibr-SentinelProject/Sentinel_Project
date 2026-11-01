"""Setup for the functional tests: the real Flask app, with repositories that keep everything in memory.

Only the repository classes are replaced (in app/services/factory.py), so the routes, services and
templates are the real ones and no database is needed.
"""
import pytest

from app import create_app
from app.models.user import Analyst, Employee
from app.services import factory


class FakeUserRepo:
    def __init__(self):
        self.users = []

    def create(self, user):
        self.users.append(user)
        return user

    def get_all(self):
        return self.users

    def get_by_id(self, user_id):
        return next((user for user in self.users if user.id == user_id), None)

    def get_by_email(self, email):
        return next((user for user in self.users if user.email == email), None)


class FakeIncidentRepo:
    def __init__(self, users):
        self.users = users
        self.incidents = []

    def create(self, incident):
        self.incidents.append(incident)
        return incident

    def get_all(self):
        # Most recent first, like the real repository.
        return [self._with_names(incident) for incident in reversed(self.incidents)]

    def get_by_id(self, incident_id):
        incident = next((item for item in self.incidents if item.id == incident_id), None)
        return self._with_names(incident) if incident else None

    def update(self, incident_id, incident):
        return incident

    def _with_names(self, incident):
        # The real repository fills these two with a JOIN.
        incident.user_name = self.users.get_by_id(incident.user_id).name
        analyst = self.users.get_by_id(incident.analyst_id) if incident.analyst_id else None
        incident.analyst_name = analyst.name if analyst else None
        return incident


class FakeCommentRepo:
    def __init__(self, users):
        self.users = users
        self.comments = []

    def create(self, comment):
        self.comments.append(comment)
        return comment

    def get_all_by_incident(self, incident_id):
        found = [comment for comment in self.comments if comment.incident_id == incident_id]
        for comment in found:
            comment.author_name = self.users.get_by_id(comment.author_id).name
        return found


@pytest.fixture
def users():
    repo = FakeUserRepo()
    for user in (Employee("Ana", "ana@example.com", "secret"),
                 Employee("Eva", "eva@example.com", "secret"),
                 Analyst("Marta", "marta@example.com", "secret")):
        repo.create(user)
    return repo


@pytest.fixture
def incidents(users):
    return FakeIncidentRepo(users)


@pytest.fixture
def client(monkeypatch, users, incidents):
    monkeypatch.setenv("SECRET_KEY", "test")
    comments = FakeCommentRepo(users)
    monkeypatch.setattr(factory, "get_db", lambda: None)
    monkeypatch.setattr(factory, "UserRepository", lambda db: users)
    monkeypatch.setattr(factory, "IncidentRepository", lambda db: incidents)
    monkeypatch.setattr(factory, "CommentRepository", lambda db: comments)
    # The server would visit the link; here the title is fixed.
    monkeypatch.setattr("app.services.incident_service.fetch_page_title", lambda url: "Titulo de la pagina")

    app = create_app()
    app.testing = True
    return app.test_client()


@pytest.fixture
def login(client):
    def login_as(email):
        return client.post("/login", data={"email": email, "password": "secret"})
    return login_as
