from uuid import UUID

from werkzeug.security import check_password_hash


class UserService:

    def __init__(self, user_repo):
        self.user_repo = user_repo

    def get_user(self, user_id: UUID):
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise LookupError("User not found")
        return user

    def login(self, email, password):
        log_user = self.user_repo.get_by_email(email)
        if log_user.password == password:
            return True
        else:
            return False

    def authenticate(self, email: str, password: str):
        """Devuelve el usuario si el email y la contraseña coinciden; si no, None."""
        user = self.user_repo.get_by_email(email)
        if user is None or not check_password_hash(user.password, password):
            return None
        return user
