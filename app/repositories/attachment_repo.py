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
        # La ruta guardada en la BD manda: los adjuntos antiguos no siguen el formato <id>.<ext>.
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

    # Un adjunto no se edita: si hay que cambiarlo, se borra y se sube otro.
    def update(self, id, entity):
        raise NotImplementedError("Attachments cannot be updated.")

    # Devuelve True si borró el adjunto o False si no existía.
    def delete(self, id: UUID):
        query = "DELETE FROM attachment WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (id,))
                # rowcount = filas borradas
                deleted = cursor.rowcount > 0
            self.db_connection.commit()
            return deleted
        except MySQLError as e:
            print(f"Error deleting attachment: {e}")
            self.db_connection.rollback()
            raise
