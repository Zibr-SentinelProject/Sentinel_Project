class User:

    def __init__(self, id, name, email, password):

        self.id = id
        self.name = name
        self.email = email
        self.password = password

    def view_all_incidents():
        pass

    def create_tickets():
        return True

class Analyst(User):

    def __init__(self):
        pass

    def view_all_incidents():
        return True


class Employee(User):

    def _init_(self):
        pass

    def view_all_incidents():
        return False

