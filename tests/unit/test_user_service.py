"""Unit tests for UserService: login, registration and who can create users.

The repository is replaced by a mock, so no database is needed.
"""
from unittest.mock import MagicMock

import pytest

from app.models.user import Admin, Analyst, Employee
from app.services.authorization import AccessDeniedError
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


def test_only_an_admin_can_create_users(service):
    employee = Employee("Ana", "ana@example.com", PASSWORD_HASH)
    analyst = Analyst("Marta", "marta@example.com", PASSWORD_HASH)
    admin = Admin("Root", "root@example.com", PASSWORD_HASH)

    for person in (employee, analyst):
        with pytest.raises(AccessDeniedError):
            service.create_user(person, "Luis", "luis@example.com", PASSWORD, "ANALYST")

    created = service.create_user(admin, "Luis", "luis@example.com", PASSWORD, "ANALYST")
    assert isinstance(created, Analyst)


def test_create_user_rejects_a_role_that_does_not_exist(service):
    admin = Admin("Root", "root@example.com", PASSWORD_HASH)

    with pytest.raises(ValueError):
        service.create_user(admin, "Luis", "luis@example.com", PASSWORD, "SUPERUSER")


def test_only_an_admin_can_list_users(service, repo):
    repo.get_all.return_value = []

    for person in (Employee("Ana", "a@example.com", "x"), Analyst("Marta", "m@example.com", "x")):
        with pytest.raises(AccessDeniedError):
            service.list_users(person)

    assert service.list_users(Admin("Root", "r@example.com", "x")) == []


def test_change_role_checks_the_permission_before_anything_else(service, repo):
    analyst = Analyst("Marta", "marta@example.com", PASSWORD_HASH)
    repo.get_by_id.return_value = None

    # The user does not exist, but a non-admin must not find that out: it is denied first.
    with pytest.raises(AccessDeniedError):
        service.change_role(analyst, "any-id", "ADMIN")


def test_change_role_rejects_a_role_that_does_not_exist(service, repo):
    admin = Admin("Root", "root@example.com", PASSWORD_HASH)

    with pytest.raises(ValueError):
        service.change_role(admin, "any-id", "SUPERUSER")
    repo.update_role.assert_not_called()


def test_change_role_of_a_missing_user_raises_lookup_error(service, repo):
    admin = Admin("Root", "root@example.com", PASSWORD_HASH)
    repo.get_by_id.return_value = None

    with pytest.raises(LookupError):
        service.change_role(admin, "missing-id", "ANALYST")
    repo.update_role.assert_not_called()


def test_an_admin_changes_the_role_of_an_existing_user(service, repo):
    admin = Admin("Root", "root@example.com", PASSWORD_HASH)
    repo.get_by_id.return_value = Employee("Ana", "ana@example.com", PASSWORD_HASH)

    service.change_role(admin, "ana-id", "ANALYST")

    repo.update_role.assert_called_once_with("ana-id", "ANALYST")


def test_an_admin_cannot_change_their_own_role(service, repo):
    admin = Admin("Root", "root@example.com", PASSWORD_HASH)
    repo.get_by_id.return_value = admin

    with pytest.raises(ValueError):
        service.change_role(admin, admin.id, "EMPLOYEE")
    repo.update_role.assert_not_called()


def test_only_users_that_handle_incidents_can_receive_an_assignment(service, repo):
    analyst = Analyst("Marta", "marta@example.com", PASSWORD_HASH)
    repo.get_all.return_value = [
        Employee("Ana", "ana@example.com", PASSWORD_HASH),
        analyst,
        Admin("Root", "root@example.com", PASSWORD_HASH),
    ]

    assert service.list_assignable_users() == [analyst]
