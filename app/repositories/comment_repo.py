#Example of how Dani an Yaxche should name their repositories.
from uuid import UUID

from pymysql import MySQLError
from pymysql.cursors import DictCursor

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
                    comment.id, comment.content, comment.author_id,
                    comment.incident_id, comment.timestamp,
                ))
            self.db_connection.commit()
            return comment
        except MySQLError as e:
            print(f"Error inserting comment: {e}")
            self.db_connection.rollback()
            raise

    def get_by_id(self, comment_id: UUID):
        query = "SELECT id, content, author_id, incident_id, timestamp FROM comments WHERE id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (comment_id,))
            result = cursor.fetchone()

        if result is None:
            return None
        comment = self._row_to_comment(result)
        return comment

    def get_all_by_incident(self, incident_id: UUID):
        query = "SELECT id, content, author_id, incident_id, timestamp FROM comments WHERE incident_id = %s ORDER BY timestamp"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (incident_id,))
            results = cursor.fetchall()
        return [self._row_to_comment(result) for result in results]

    def update(self, id: UUID, comment: Comment):
        query = "UPDATE comments SET content = %s WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (comment.content, id))
            self.db_connection.commit()
            return comment
        except MySQLError as e:
            print(f"Error updating comment: {e}")
            self.db_connection.rollback()
            raise

    def delete(self, id: UUID):
        query = "DELETE FROM comments WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (id,))
                # rowcount = filas borradas
                deleted = cursor.rowcount > 0
            self.db_connection.commit()
            return deleted
        except MySQLError as e:
            print(f"Error deleting comment: {e}")
            self.db_connection.rollback()
            raise
