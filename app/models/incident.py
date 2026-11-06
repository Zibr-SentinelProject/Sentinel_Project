from datetime import datetime
import uuid

from app.models.attachment import Attachment

class Incident:
    """A security incident reported by a user. It has a severity, a state and, optionally, an analyst."""

    # Ids of the con_state and con_severity tables (see init.sql)
    OPEN = 1
    PENDING = 2
    CLOSED = 3

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __init__(self, user_id: uuid.UUID, title: str, description: str, severity: int,
                 id: uuid.UUID = None, state: int = None, open_date: datetime = None,
                 close_date: datetime = None, analyst_id: uuid.UUID = None,
                 user_name: str = None, analyst_name: str = None,
                 source_url: str = None, source_title: str = None, attachment: Attachment = None):
        """Creates an incident.

        Args:
            user_id (uuid.UUID): The user who reports the incident
            title (str): The title of the incident
            description (str): The description of the incident
            severity (int): The severity (LOW, MEDIUM, HIGH or CRITICAL)
            id (uuid.UUID, optional): Only used when the incident comes from the database. Defaults to None.
            state (int, optional): The state (OPEN, PENDING or CLOSED). Defaults to None.
            open_date (datetime, optional): The date the incident was opened. Defaults to None.
            close_date (datetime, optional): The date the incident was closed. Defaults to None.
            analyst_id (uuid.UUID, optional): The analyst assigned to the incident. Defaults to None.
            user_name (str, optional): The name of the user who reported it, only filled when reading
                from the database. Defaults to None.
            analyst_name (str, optional): The name of the assigned analyst, only filled when reading
                from the database. Defaults to None.
            source_url (str, optional): A link related to the incident. Defaults to None.
            source_title (str, optional): The title of the page of the source_url. Defaults to None.
            attachment (Attachment, optional): The file attached to the incident. Defaults to None.
        """
        self.id = id or uuid.uuid4()
        self.user_id = user_id
        # Optional file that is saved together with the ticket when it is created (one per incident).
        self.attachment = attachment
        # Optional external link and the page title, which the server fetches when the ticket is created.
        self.source_url = source_url
        self.source_title = source_title
        # Names of the creator and the analyst; only filled in when the repository does a JOIN with user.
        self.user_name = user_name
        self.analyst_name = analyst_name
        self.title = title
        self.description = description
        self.open_date = open_date or datetime.today().replace(microsecond=0)
        # These four are private: they only change through assign() and change_state().
        self._severity = severity
        self._state = state or self.OPEN
        self._close_date = close_date
        self._analyst_id = analyst_id

    @property
    def severity(self) -> int:
        """The severity of the incident (LOW, MEDIUM, HIGH or CRITICAL)."""
        return self._severity

    @property
    def state(self) -> int:
        """The state of the incident. It only changes with assign() and change_state()."""
        return self._state

    @property
    def close_date(self) -> datetime:
        """The date the incident was closed, or None if it is still not closed."""
        return self._close_date

    @property
    def analyst_id(self) -> uuid.UUID:
        """The analyst assigned to the incident, or None if nobody has taken it yet."""
        return self._analyst_id

    def is_closed(self) -> bool:
        """Tells if the incident is closed.

        Returns:
            bool: True if the state is CLOSED, False if not.
        """
        return self.state == self.CLOSED

    @property
    def severity_name(self) -> str:
        """The severity as text (LOW, MEDIUM, HIGH or CRITICAL), to show it to the user."""
        return {self.LOW: "LOW", self.MEDIUM: "MEDIUM", self.HIGH: "HIGH", self.CRITICAL: "CRITICAL"}[self.severity]

    @property
    def severity_key(self) -> str:
        """Lowercase name, for the badge CSS class (badge-low, badge-high...)."""
        return self.severity_name.lower()

    @property
    def state_name(self) -> str:
        """The state as text (OPEN, PENDING or CLOSED), to show it to the user."""
        return {self.OPEN: "OPEN", self.PENDING: "PENDING", self.CLOSED: "CLOSED"}[self.state]

    def assign(self, analyst_id: uuid.UUID):
        """Assigns the incident to an analyst. An OPEN incident becomes PENDING.

        Args:
            analyst_id (uuid.UUID): The analyst who takes the incident

        Raises:
            ValueError: If the incident is closed, or if the analyst is the one who reported it
        """
        if self.is_closed():
            raise ValueError("A closed incident cannot be assigned")
        if analyst_id == self.user_id:
            raise ValueError("An analyst cannot be assigned their own incident")
        self._analyst_id = analyst_id
        # An open ticket becomes pending as soon as it has an analyst; reassigning keeps its state.
        if self.state == self.OPEN:
            self._state = self.PENDING

    def change_state(self, new_state: int):
        """Changes the state of the incident. If the new state is CLOSED, it saves the close date.

        Args:
            new_state (int): OPEN, PENDING or CLOSED

        Raises:
            ValueError: If the state is not valid
        """
        if new_state not in (self.OPEN, self.PENDING, self.CLOSED):
            raise ValueError("Invalid state")
        self._state = new_state
        if new_state == self.CLOSED:
            self._close_date = datetime.today().replace(microsecond=0)

    def close(self):
        """Closes the incident (shortcut for change_state(CLOSED))."""
        self.change_state(self.CLOSED)
