from datetime import datetime
import uuid

from user import user, analyst

print(datetime.today())

class incident:

    STATES = ["OPEN", "PENDIG", "COLSE"]
    SEVERITIS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def __init__(self, user:user, title, description, severity):
        self.id = str(uuid.uuid4())
        self.id_user = user.id
        self.title = title
        self.description = description
        self.severity = severity
        self.state = 0
        self.open_date = datetime.today()
        self.close_date = None
        self.id_analyst = None

    def close(self):
        self.close_date = datetime.today()

    def assign(self, user:analyst):
        self.id_analyst = user.id