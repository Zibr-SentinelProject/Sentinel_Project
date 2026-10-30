from uuid import UUID

from app.models.user import ROLE_CLASSES, User


class UserService:

    def __init__(self, user_repo):
        self.user_repo = user_repo

    def get_user(self, user_id: UUID):
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise LookupError("User not found")
        return user

    def list_analysts(self):
        """Los usuarios a los que se puede asignar un ticket."""
        return [user for user in self.user_repo.get_all() if user.is_analyst()]

    def create_user(self, person: User, name: str, email: str, password: str, role: str):
        """Solo un analista puede crear usuarios y elegir su rol."""
        if not person.is_analyst():
            raise PermissionError("Only analysts can create users")
        if role not in ROLE_CLASSES:
            raise ValueError("Invalid role")
        if self.user_repo.get_by_email(email) is not None:
            raise ValueError("Email already registered")

        user_class = ROLE_CLASSES[role]
        new_user = user_class(name, email, password)
        return self.user_repo.create(new_user)

    def change_password(self, user: User, current_password: str, new_password: str):
        """Cada usuario cambia su propia contraseña, confirmando primero la actual."""
        if user.password != current_password:
            raise ValueError("Current password is incorrect")
        if not new_password:
            raise ValueError("New password is required")

        user.password = new_password
        return self.user_repo.update(user.id, user)

    def authenticate(self, email: str, password: str):
        """Devuelve el usuario si el email y la contraseña coinciden; si no, None."""
        user = self.user_repo.get_by_email(email)
        if user is None or user.password != password:
            return None
        return user
