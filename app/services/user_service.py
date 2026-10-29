from uuid import UUID
from app.models.user import User

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
        