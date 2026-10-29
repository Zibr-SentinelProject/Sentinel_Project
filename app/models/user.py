import uuid


class User:
    ROLE = None

    def __init__(self, name, email, password, id=None):
        self.id = id or uuid.uuid4()
        self.name = name
        self.email = email
        self.password = password

    def view_all_incidents(self):
        pass

    def create_tickets(self):
        return True

    def is_analyst(self) -> bool:
        return False

    def __eq__(self, other):

        if not isinstance(other, User):
            return False
        elif self.id == other.id and self.email == other.email:
            return True

        return False

    def __hash__(self):
        return hash(self.id)

    def get_rol(self):
        return self.ROLE
    
class Analyst(User):

    ROLE = "ANALYST"

    def view_all_incidents(self):
        return True

    def is_analyst(self) -> bool:
        return True


class Employee(User):

    ROLE = "EMPLOYEE"

    def view_all_incidents(self):
        return False


ROLE_CLASSES = {
    Analyst.ROLE: Analyst,
    Employee.ROLE: Employee,
}
