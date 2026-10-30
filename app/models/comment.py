from datetime import datetime
from uuid import UUID, uuid4

class Comment():
    def __init__(self, content, author_id: UUID, incident_id: UUID, id: UUID = None, timestamp: datetime = None,
                 author_name: str = None):
        self.id = id or uuid4()
        self.content = content
        self.author_id = author_id
        # Solo viene rellenado cuando el repositorio lee el comentario con su autor (JOIN con user).
        self.author_name = author_name
        self.incident_id = incident_id
        self.timestamp = timestamp or datetime.now()
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")


    def __repr__(self):
        return f"<Comment by {self.author_id}: {self.content}>"
