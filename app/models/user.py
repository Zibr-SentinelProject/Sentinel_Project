import uuid


class User:
    """this is the users class
    """
    ROLE = None

    def __init__(self, name, email, password, id=None):
        """

        Args:
            name (str): The user's name.
            email (str): The user's email.
            password (str): The user's password.
            id (uuid): The user's id.
        """
        self.id = id or uuid.uuid4()
        self.name = name
        self.email = email
        self.password = password

    def view_all_incidents(self):
        """It's a permission to know if the user can or not depending of its role.
        """
        pass

    def create_tickets(self):
        """It's a permission to know if the user can or not.

        Returns:
            _type_: _description_
        """
        return True

    def is_analyst(self) -> bool:
        """to know if the user is an analyst or not

        Returns:
            bool: False if the user isn't analyst, true if the user is an analyst.
        """
        return False

    def __eq__(self, other):
        """Equals to ensure that we're not using the same user.

        Args:
            other (object): is how we call User1 to compare it to the User2 

        Returns:
            bool: Returns True in case that User1 and User2 are equals and false in case that they're not.
        """

        if not isinstance(other, User):
            return False
        elif self.id == other.id and self.email == other.email:
            return True

        return False

    def __hash__(self):
        return hash(self.id)

    def get_role(self):
        """Function to get the User's role

        Returns:
            str: The user's role.
        """
        return self.ROLE
    
class Analyst(User):
    """is the subclass analyst of User

    Args:
        User (Class): The parent Class
    """

    ROLE = "ANALYST"

    def view_all_incidents(self):
        """Is a permission to let the analyst view the incidents

        Returns:
            bool: Is true because an analyst can
        """
        return True

    def is_analyst(self) -> bool:
        return True


class Employee(User):
    """Is the subclass Employee of User

    Args:
        User (Class): The parent class
    """

    ROLE = "EMPLOYEE"

    def view_all_incidents(self):
        """Is a permission to deny the employees to view all incidents

        Returns:
            bool: Is False becouse an employee can't
        """
        return False


ROLE_CLASSES = {
    Analyst.ROLE: Analyst,
    Employee.ROLE: Employee,
}
