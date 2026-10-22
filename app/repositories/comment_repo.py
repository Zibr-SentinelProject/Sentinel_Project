#Example of how Dani an Yaxche should name their repositories.
from uuid import UUID

import pymysql.cursors

from app.repositories.abc_repo import RepositoryABC
from app.models.comment import Comment

class CommentRepository (RepositoryABC):

    def _row_to_comment(self, row: dict) -> Comment:
        """Convert a database row (dict) into a Comment object."""
        return Comment(
            id=UUID(str(row["id"])),
            content=row["content"],
            author_id=UUID(str(row["author_id"])),
            incident_id=UUID(str(row["incident_id"])),
            timestamp=row["timestamp"],
        )

    def create(self, comment: Comment):
        query = "INSERT INTO comments (id, content, author_id, incident_id, timestamp) VALUES (%s, %s, %s, %s, %s)"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    str(comment.id), comment.content, str(comment.author_id),
                    str(comment.incident_id), comment.timestamp,
                ))
            self.db_connection.commit()
            return comment
        except pymysql.MySQLError as e:
            print(f"Error inserting comment: {e}")
            self.db_connection.rollback()
            raise

    def get_by_id(self, comment_id: UUID):
        query = "SELECT id, content, author_id, incident_id, timestamp FROM comments WHERE id = %s"
        with self.db_connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, (str(comment_id),))
            result = cursor.fetchone()
        return self._row_to_comment(result) if result else None

    def get_all_by_incident(self, incident_id: UUID):
        query = "SELECT id, content, author_id, incident_id, timestamp FROM comments WHERE incident_id = %s ORDER BY timestamp"
        with self.db_connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, (str(incident_id),))
            results = cursor.fetchall()
        return [self._row_to_comment(result) for result in results]

    def update(self, id, entity):
        raise NotImplementedError("Subclasses must implement this method.")

    def delete(self, id):
        raise NotImplementedError("Subclasses must implement this method.")
