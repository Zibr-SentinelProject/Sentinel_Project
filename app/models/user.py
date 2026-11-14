import uuid
import warnings


class User:
    """A person who uses Sentinel. It is the parent of Analyst, Employee and Admin.

    Each subclass sets its own ROLE and decides what the user can do.
    """
    ROLE = None

    def __init__(self, name, email, password, id=None):
        """Creates a user.

        Args:
            name (str): The user's name.
            email (str): The user's email.
            password (str): The user's password.
            id (uuid, optional): Only used when the user comes from the database.
                If it is not given, a new one is created.
        """
        self.id = id or uuid.uuid4()
        self.name = name
        self.email = email
        self._password = password

    @property
    def password(self):
        """The user's password. It can be read, but only changed with change_password."""
        return self._password

    def change_password(self, new_password: str):
        """The only way to change the password."""
        self._password = new_password

    def view_all_incidents(self):
        """Permission to know if the user can see all the incidents, depending on its role.

        Returns:
            bool: False by default. Subclasses override it to allow it.
        """
        return False

    def handle_incidents(self):
        """Permission to know if the user can be assigned to, close and comment on incidents.

        Returns:
            bool: False by default. Subclasses override it to allow it.
        """
        return False

    def create_tickets(self):
        """Permission to know if the user can create incidents.

        Returns:
            bool: True, because every user can create incidents.
        """
        return True

    def is_analyst(self) -> bool:
        """DEPRECATED: ask for a capability instead (handle_incidents, admin_all_users).

        Returns:
            bool: False if the user isn't an analyst, True if the user is an analyst.
        """
        warnings.warn(
            "is_analyst() is deprecated; use a capability instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return False
    
    def admin_all_users(self):
        """Permission to know if the user can manage all the users, depending on its role.

        Returns:
            bool: False by default. Subclasses override it to allow it.
        """
        return False

    def __eq__(self, other):
        """Compares two users. They are the same user if they have the same id and the same email.

        Args:
            other (object): The other object to compare with this user.

        Returns:
            bool: True if both are users with the same id and email, False if not.
        """

        if not isinstance(other, User):
            return False
        elif self.id == other.id and self.email == other.email:
            return True

        return False

    def __hash__(self):
        """Uses the id, so users can be stored in sets and dictionaries."""
        return hash(self.id)

    def get_role(self):
        """Gets the user's role.

        Returns:
            str: The user's role.
        """
        return self.ROLE

class Analyst(User):
    """A user who handles incidents: can see all of them, and be assigned to, comment on and close them.

    Args:
        User (Class): The parent class
    """

    ROLE = "ANALYST"

    def view_all_incidents(self):
        """Permission to let the analyst view all the incidents.

        Returns:
            bool: True, because an analyst can.
        """
        return True

    def is_analyst(self) -> bool:
        """DEPRECATED: ask for a capability instead (handle_incidents, admin_all_users).

        Returns:
            bool: True, always.
        """
        warnings.warn(
            "is_analyst() is deprecated; use a capability instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return True

    def admin_all_users(self) -> bool:
        """Permission to let the analyst manage all the users.

        Returns:
            bool: False, because an analyst can't.
        """
        return False

    def handle_incidents(self):
        """Permission to let the analyst be assigned to, close and comment on incidents.

        Returns:
            bool: True, because an analyst can.
        """
        return True

class Employee(User):
    """A user who reports incidents. It can only see the incidents it created.

    Args:
        User (Class): The parent class
    """

    ROLE = "EMPLOYEE"

    def view_all_incidents(self):
        """Permission that denies the employee to view all the incidents.

        Returns:
            bool: False, because an employee can't.
        """
        return False

    def admin_all_users(self):
        """Permission that denies the employee to manage all the users.

        Returns:
            bool: False, because an employee can't.
        """
        return False

    def handle_incidents(self):
        """Permission that denies the employee to be assigned to, close and comment on incidents.

        Returns:
            bool: False, because an employee can't.
        """
        return False

class Admin(User):
    """A user who manages the system. It can see all the incidents and manage the users.

    Args:
        User (Class): The parent class
    """

    ROLE = "ADMIN"

    def view_all_incidents(self):
        """Permission to let the admin view all the incidents.

        Returns:
            bool: True, because an admin can.
        """
        return True

    def admin_all_users(self):
        """Permission to let the admin manage all the users.

        Returns:
            bool: True, because an admin can.
        """
        return True
    

ROLE_CLASSES = {
    Analyst.ROLE: Analyst,
    Employee.ROLE: Employee,
    Admin.ROLE: Admin,
}
