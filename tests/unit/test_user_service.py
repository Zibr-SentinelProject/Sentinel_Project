"""Unit tests for UserService: login, registration and who can create users.

The repository is replaced by a mock, so no database is needed.
"""
from unittest.mock import MagicMock

import pytest

from app.models.user import Analyst, Employee
from app.services.user_service import UserService
from app.utils.security import hash_password

# Valid password (8+ characters), hashed once because bcrypt is slow on purpose.
PASSWORD = "secret123"
PASSWORD_HASH = hash_password(PASSWORD)


@pytest.fixture
def repo():
    repo = MagicMock()
    repo.create.side_effect = lambda user: user
    repo.get_by_email.return_value = None
    return repo


@pytest.fixture
def service(repo):
    return UserService(repo)


def test_authenticate_returns_the_user_when_email_and_password_match(service, repo):
    user = Employee("Ana", "ana@example.com", PASSWORD_HASH)
    repo.get_by_email.return_value = user

    assert service.authenticate("ana@example.com", PASSWORD) is user


def test_authenticate_returns_none_with_a_wrong_password(service, repo):
    repo.get_by_email.return_value = Employee("Ana", "ana@example.com", PASSWORD_HASH)

    assert service.authenticate("ana@example.com", "otra") is None


def test_register_always_creates_an_employee(service):
    user = service.register("Ana", "ana@example.com", PASSWORD)

    assert isinstance(user, Employee)


def test_only_an_analyst_can_create_users(service):
    employee = Employee("Ana", "ana@example.com", PASSWORD_HASH)

    with pytest.raises(PermissionError):
        service.create_user(employee, "Luis", "luis@example.com", PASSWORD, "ANALYST")

    analyst = Analyst("Marta", "marta@example.com", PASSWORD_HASH)
    created = service.create_user(analyst, "Luis", "luis@example.com", PASSWORD, "ANALYST")
    assert isinstance(created, Analyst)
