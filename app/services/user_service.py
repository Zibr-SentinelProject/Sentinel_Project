from uuid import UUID

from app.models.user import Employee, ROLE_CLASSES, User
from app.utils.security import hash_password, verify_password

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72

_DUMMY_HASH = hash_password("potato_team")


class UserService:
    """Rules for the users: who can register, create and see them."""

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

    def list_analysts(self):
        """Users a ticket can be assigned to."""
        return [user for user in self.user_repo.get_all() if user.is_analyst()]

    def register(self, name: str, email: str, password: str):
        """Anyone can register, but the account is always an employee.
        Only an analyst can give the analyst role (see create_user)."""
        self._check_email_is_free(email)
        self._check_password_is_valid(password)
        pass_hashed = hash_password(password)
        new_user = Employee(name, email, pass_hashed)
        return self.user_repo.create(new_user)

    def create_user(self, person: User, name: str, email: str, password: str, role: str):
        """Only an analyst can create users and choose their role."""
        if not person.is_analyst():
            raise PermissionError("Only analysts can create users")
        if role not in ROLE_CLASSES:
            raise ValueError("Invalid role")
        self._check_email_is_free(email)
        self._check_password_is_valid(password)

        user_class = ROLE_CLASSES[role]
        pass_hashed = hash_password(password)
        new_user = user_class(name, email, pass_hashed)
        return self.user_repo.create(new_user)

    def list_users(self, person: User):
        """Only analysts can see the list of users."""
        if not person.is_analyst():
            raise PermissionError("Only analysts can list users")
        return self.user_repo.get_all()

    def change_role(self, person: User, user_id: UUID, role: str):
        """Only an analyst can give or take away the analyst role."""
        if not person.is_analyst():
            raise PermissionError("Only analysts can change roles")
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
