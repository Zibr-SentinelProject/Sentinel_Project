from uuid import UUID

from app.models.user import ROLE_CLASSES, User


class UserService:

    def __init__(self, user_repo):
        self.user_repo = user_repo

    def get_user(self, user_id: UUID):
        """This functions validate if a user exists
        Args:
            user_id (UUID): The user id.

        Returns:
            str: it says user if it exists and User not found if not.
        """
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise LookupError("User not found")
        return user

    def create_user(self, person: User, name: str, email: str, password: str, role: str):
        """This function validates that the user that made the requests is allowed to create users and validates that the email given doesn't exists in other user yet. and gives the repository the parametters to create the user.

        Args:
            person (User): user that made the request
            name (str): username
            email (str): user email
            password (str): user password
            role (str): user role

        Raises:
            PermissionError: it appears if the user that made the request isn't allowed to create users.
            ValueError: it appears if the role given doesn't exists
            ValueError: it appears if email given does exists in another user.
        """
        if not person.is_analyst():
            raise PermissionError("Only analysts can create users")
        if role not in ROLE_CLASSES:
            raise ValueError("Invalid role")
        if self.user_repo.get_by_email(email) is not None:
            raise ValueError("Email already registered")

        user_class = ROLE_CLASSES[role]
        new_user = user_class(name, email, password)
        return self.user_repo.create(new_user)

    def authenticate(self, email: str, password: str):
        """it returns user if the user exists if not it returns none."""
        user = self.user_repo.get_by_email(email)
        if user is None or user.password != password:
            return None
        return user
