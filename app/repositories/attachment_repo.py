from uuid import UUID

from pymysql import MySQLError
from pymysql.cursors import DictCursor

from app.repositories.abc_repo import RepositoryABC
from app.models.attachment import Attachment

class AttachmentRepository (RepositoryABC):

    def _row_to_attachment(self, row: dict) -> Attachment:
        """Convert a database row (dict) into an Attachment object."""
        attachment = Attachment(
            id=UUID(str(row["id"])),
            incident_id=UUID(str(row["incident_id"])),
            filename=row["filename"],
            filetype=row["filetype"],
            filesize=row["filesize"],
        )
        # The path stored in the DB takes precedence: old attachments don't follow the <id>.<ext> format.
        attachment.path = row["path"]
        return attachment

    def create(self, attachment: Attachment):
        query = (
            "INSERT INTO attachment (id, incident_id, filename, filetype, filesize, path) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    attachment.id, attachment.incident_id, attachment.filename,
                    attachment.filetype, attachment.filesize, attachment.path,
                ))
            self.db_connection.commit()
            return attachment
        except MySQLError as e:
            print(f"Error inserting attachment: {e}")
            self.db_connection.rollback()
            raise

    def get_by_id(self, attachment_id: UUID):
        query = "SELECT id, incident_id, filename, filetype, filesize, path FROM attachment WHERE id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (attachment_id,))
            result = cursor.fetchone()
        return self._row_to_attachment(result) if result else None

    def get_all_by_incident(self, incident_id: UUID):
        query = "SELECT id, incident_id, filename, filetype, filesize, path FROM attachment WHERE incident_id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (incident_id,))
            results = cursor.fetchall()
        return [self._row_to_attachment(result) for result in results]

    # An attachment is never edited: to change it, delete it and upload another one.
    def update(self, id, entity):
        raise NotImplementedError("Attachments cannot be updated.")

    # Returns True if the attachment was deleted or False if it did not exist.
    def delete(self, id: UUID):
        query = "DELETE FROM attachment WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (id,))
                # rowcount = deleted rows
                deleted = cursor.rowcount > 0
            self.db_connection.commit()
            return deleted
        except MySQLError as e:
            print(f"Error deleting attachment: {e}")
            self.db_connection.rollback()
            raise
