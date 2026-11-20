from uuid import UUID

from app.models.user import Employee, ROLE_CLASSES, User
from app.services.authorization import BE_ASSIGNEE, MANAGE_USERS, authorize, require
from app.utils.security import hash_password, verify_password

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72

_DUMMY_HASH = hash_password("potato_team")


class UserService:
    """Rules for the users: who can register, create and see them.

    Deleting users is not implemented, to avoid orphan tickets: incidents point to the user who
    created them and to the analyst assigned to them, and they would be left without an owner.
    """

    def __init__(self, user_repo):
        """Creates the service.

        Args:
            user_repo (UserRepository): Used to save and read the users
        """
        self.user_repo = user_repo

    def get_user(self, user_id: UUID):
        """Gets a user by its UUID.

        Args:
            user_id (UUID): The UUID of the user

        Raises:
            LookupError: If the user does not exist

        Returns:
            user (User): The user found
        """
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise LookupError("User not found")
        return user

    def list_assignable_users(self):
        """Users a ticket can be assigned to (the ones that can receive an assignment)."""
        return [user for user in self.user_repo.get_all() if authorize(user, BE_ASSIGNEE)]

    def register(self, name: str, email: str, password: str):
        """Anyone can register, but the account is always an employee.
        Only whoever manages the users can choose another role (see create_user)."""
        self._check_email_is_free(email)
        self._check_password_is_valid(password)
        pass_hashed = hash_password(password)
        new_user = Employee(name, email, pass_hashed)
        return self.user_repo.create(new_user)

    def create_user(self, person: User, name: str, email: str, password: str, role: str):
        """Only whoever manages the users can create them and choose their role.

        On hold: the route that used this method (POST /users/new) is commented out. Anyone can already
        register freely and an admin can change roles, so keeping that route would make the attack surface
        bigger without any benefit.
        """
        require(person, MANAGE_USERS)
        if role not in ROLE_CLASSES:
            raise ValueError("Invalid role")
        self._check_email_is_free(email)
        self._check_password_is_valid(password)

        user_class = ROLE_CLASSES[role]
        pass_hashed = hash_password(password)
        new_user = user_class(name, email, pass_hashed)
        return self.user_repo.create(new_user)

    def list_users(self, person: User):
        """Only whoever manages the users can see the list of users."""
        require(person, MANAGE_USERS)
        return self.user_repo.get_all()

    def change_role(self, person: User, user_id: UUID, role: str):
        """Only whoever manages the users can change a role. The role must be one of ROLE_CLASSES.

        Raises:
            AccessDeniedError: If the person cannot manage users (checked first, so it never reveals if the user exists)
            ValueError: If the person tries to change their own role, or the role is not valid
            LookupError: If the user does not exist
        """
        require(person, MANAGE_USERS)
        # Nobody changes their own role: this way there is always at least one admin left.
        if user_id == person.id:
            raise ValueError("You cannot change your own role")
        if role not in ROLE_CLASSES:
            raise ValueError("Invalid role")
        # get_user raises LookupError if the user does not exist.
        self.get_user(user_id)
        self.user_repo.update_role(user_id, role)

    def change_password(self, user: User, current_password: str, new_password: str):
        """Each user changes their own password, confirming the current one first."""
        if not verify_password(current_password, user.password):
            raise ValueError("Current password is incorrect")
        self._check_password_is_valid(new_password)
        pass_hashed = hash_password(new_password)
        user.change_password(pass_hashed)
        return self.user_repo.update(user.id, user)

    def authenticate(self, email: str, password: str):
        """Return the user if the email and password match; otherwise None."""
        user = self.user_repo.get_by_email(email)
        if user is None:
            # Spend the same time as a real check so timing does not reveal
            # which emails are registered.
            verify_password(password, _DUMMY_HASH)
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def _check_password_is_valid(self, password: str):
        """Same password rules for register, create_user and change_password."""
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
            )
        if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password must be at most {MAX_PASSWORD_BYTES} bytes"
            )

    def _check_email_is_free(self, email: str):
        """Two accounts cannot share an email (used by register and create_user)."""
        if self.user_repo.get_by_email(email) is not None:
            raise ValueError("Email already registered")
