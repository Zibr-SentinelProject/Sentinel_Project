#Example of how Dani an Yaxche should name their repositories.
from uuid import UUID

from pymysql import MySQLError
from pymysql.cursors import DictCursor

from app.repositories.abc_repo import RepositoryABC
from app.models.comment import Comment

class CommentRepository (RepositoryABC):

    def _row_to_comment(self, row: dict) -> Comment:
        """Turns a database row into a Comment.

        Args:
            row (dict): The row of the comment table

        Returns:
            comment (Comment): The comment built from the row
        """
        return Comment(
            id=UUID(str(row["id"])),
            content=row["content"],
            author_id=UUID(str(row["author_id"])),
            incident_id=UUID(str(row["incident_id"])),
            timestamp=row["timestamp"],
            author_name=row.get("author_name"),
        )

    def create(self, comment: Comment):
        """Saves a comment in the database.

        Args:
            comment (Comment): The comment to save

        Returns:
            comment (Comment): The comment saved
        """
        query = "INSERT INTO comment (id, content, author_id, incident_id, timestamp) VALUES (%s, %s, %s, %s, %s)"
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
        """Gets a comment by its UUID.

        Args:
            comment_id (UUID): The UUID of the comment

        Returns:
            comment (Comment): The comment, or None if it does not exist
        """
        query = "SELECT id, content, author_id, incident_id, timestamp FROM comment WHERE id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (comment_id,))
            result = cursor.fetchone()

        if result is None:
            return None
        comment = self._row_to_comment(result)
        return comment

    def get_all_by_incident(self, incident_id: UUID):
        """Gets all the comments of an incident.

        Args:
            incident_id (UUID): The UUID of the incident

        Returns:
            comments (List): The comments with the name of their author, from oldest to newest
        """
        query = (
            "SELECT c.id, c.content, c.author_id, c.incident_id, c.timestamp, u.name AS author_name "
            "FROM comment c INNER JOIN user u ON u.id = c.author_id "
            "WHERE c.incident_id = %s ORDER BY c.timestamp"
        )
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (incident_id,))
            results = cursor.fetchall()
        return [self._row_to_comment(result) for result in results]

    def update(self, id: UUID, comment: Comment):
        """Changes the text of a comment.

        Args:
            id (UUID): The UUID of the comment to update
            comment (Comment): The comment with the new text

        Returns:
            comment (Comment): The comment updated
        """
        query = "UPDATE comment SET content = %s WHERE id = %s"
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
        """Deletes a comment.

        Args:
            id (UUID): The UUID of the comment to delete

        Returns:
            deleted (bool): True if the comment was deleted, False if it did not exist
        """
        query = "DELETE FROM comment WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (id,))
                # rowcount = deleted rows
                deleted = cursor.rowcount > 0
            self.db_connection.commit()
            return deleted
        except MySQLError as e:
            print(f"Error deleting comment: {e}")
            self.db_connection.rollback()
            raise
