from datetime import datetime
import uuid


class Incident:


    # Ids de las tablas con_state y con_severity (ver init.sql)
    OPEN = 1
    PENDING = 2
    CLOSED = 3

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __init__(self, user_id: uuid.UUID, title: str, description: str, severity: int,
                 id: uuid.UUID = None, state: int = None, open_date: datetime = None,
                 close_date: datetime = None, analyst_id: uuid.UUID = None):
        self.id = id or uuid.uuid4()
        self.user_id = user_id
        self.analyst_id = None
        self.title = title
        self.description = description
        self.severity = severity
        self.state = state or self.OPEN
        self.open_date = open_date or datetime.today().replace(microsecond=0)
        self.close_date = close_date
        self.analyst_id = analyst_id

    def is_closed(self) -> bool:
        return self.state == self.CLOSED

    def assign(self, analyst_id: uuid.UUID):
        if self.is_closed():
            raise ValueError("A closed incident cannot be assigned")
        if analyst_id == self.user_id:
            raise ValueError("An analyst cannot be assigned their own incident")
        self.analyst_id = analyst_id

    def change_state(self, new_state: int):
        if new_state not in (self.OPEN, self.PENDING, self.CLOSED):
            raise ValueError("Invalid state")
        self.state = new_state
        if new_state == self.CLOSED:
            self.close_date = datetime.today().replace(microsecond=0)

    def close(self):
        self.change_state(self.CLOSED)
