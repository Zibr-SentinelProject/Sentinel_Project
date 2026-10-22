import uuid

class user:

    def __init__(self, id, name, email, password):

        self.id = uuid.uuid4()
        self.name = name
        self.email = email
        self.password = password

    def view_all_incidents():
        pass

    def create_tickets():
        return True

    def __eq__(self, other):

        if not isinstance(other,user):
            return False
        elif self.id == other.id and self.email == other.email:
            return True
        
        return False
        
class analyst(user):

    def __init__(self):
        pass

    def view_all_incidents():
        return True


class employee(user):

    def _init_(self):
        pass

    def view_all_incidents():
        return False

