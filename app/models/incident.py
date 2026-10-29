from datetime import datetime
import uuid

from app.models.user import Analyst

class Incident:

    STATES = ["OPEN", "PENDIG", "COLSED"]
    SEVERITIS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def __init__(self, user_id: uuid, title: str, description: str, severity: int):
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.title = title
        self.description = description
        self.severity = severity
        self.state = 0
        self.open_date = datetime.today().replace(microsecond=0)
        self.close_date = None
        self.analyst_id = None

    def is_closed(self) -> bool:
        return self.state == self.CLOSED

    def assign(self, analyst_id: uuid.UUID):
        if self.is_closed():
            raise ValueError("A closed incident cannot be assigned")
        if analyst_id == self.user_id:
            raise ValueError("An analyst cannot be assigned their own incident")
        self.analyst_id = analyst_id

    def change_state(self, new_state: int):
        if new_state not in range(len(self.STATES)):
            raise ValueError("Invalid state")
        self.state = new_state
        if new_state == self.CLOSED:
            self.close_date = datetime.today().replace(microsecond=0)

    def close(self):
        self.change_state(self.CLOSED)