from datetime import datetime
from uuid import UUID, uuid4

class Comment():
    """A comment written on an incident."""

    def __init__(self, content, author_id: UUID, incident_id: UUID, id: UUID = None, timestamp: datetime = None,
                 author_name: str = None):
        """Creates a comment.

        Args:
            content (str): The text of the comment
            author_id (UUID): The user who writes the comment
            incident_id (UUID): The incident that is commented
            id (UUID, optional): Only used when the comment comes from the database. Defaults to None.
            timestamp (datetime, optional): The date of the comment. Defaults to now.
            author_name (str, optional): The name of the author, only filled when reading from the database.
                Defaults to None.

        Raises:
            ValueError: If the content is empty
        """
        self.id = id or uuid4()
        self.content = content
        self.author_id = author_id
        # Only filled in when the repository reads the comment together with its author (JOIN with user).
        self.author_name = author_name
        self.incident_id = incident_id
        self.timestamp = timestamp or datetime.now()
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")


    def __repr__(self):
        return f"<Comment by {self.author_id}: {self.content}>"
