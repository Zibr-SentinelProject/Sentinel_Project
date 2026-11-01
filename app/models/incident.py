from datetime import datetime
import uuid


class Incident:


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
                 source_url: str = None, source_title: str = None, attachment=None):
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
        return self._severity

    @property
    def state(self) -> int:
        return self._state

    @property
    def close_date(self) -> datetime:
        return self._close_date

    @property
    def analyst_id(self) -> uuid.UUID:
        return self._analyst_id

    def is_closed(self) -> bool:
        return self.state == self.CLOSED

    @property
    def severity_name(self) -> str:
        return {self.LOW: "LOW", self.MEDIUM: "MEDIUM", self.HIGH: "HIGH", self.CRITICAL: "CRITICAL"}[self.severity]

    @property
    def severity_key(self) -> str:
        """Lowercase name, for the badge CSS class (badge-low, badge-high...)."""
        return self.severity_name.lower()

    @property
    def state_name(self) -> str:
        return {self.OPEN: "OPEN", self.PENDING: "PENDING", self.CLOSED: "CLOSED"}[self.state]

    def assign(self, analyst_id: uuid.UUID):
        if self.is_closed():
            raise ValueError("A closed incident cannot be assigned")
        if analyst_id == self.user_id:
            raise ValueError("An analyst cannot be assigned their own incident")
        self._analyst_id = analyst_id

    def change_state(self, new_state: int):
        if new_state not in (self.OPEN, self.PENDING, self.CLOSED):
            raise ValueError("Invalid state")
        self._state = new_state
        if new_state == self.CLOSED:
            self._close_date = datetime.today().replace(microsecond=0)

    def close(self):
        self.change_state(self.CLOSED)
