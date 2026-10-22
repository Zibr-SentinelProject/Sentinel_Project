from datetime import datetime
import uuid

from user import user, analyst

class incident:

    STATES = ["OPEN", "PENDIG", "COLSED"]
    SEVERITIS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def __init__(self, user_id: uuid, title: str, description: str, severity: int):
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.title = title
        self.description = description
        self.severity = severity
        self.state = 0
        self.open_date = datetime.today()
        self.close_date = None
        self.analyst_id = None

    def close(self):
        self.close_date = datetime.today()
        self.state = 2
        return None

    def assign(self, analyst:analyst):

        self.state = 1
        return True