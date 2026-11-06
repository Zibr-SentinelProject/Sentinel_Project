from uuid import UUID

from pymysql import MySQLError
from pymysql.cursors import DictCursor

from app.repositories.abc_repo import RepositoryABC
from app.models.attachment import Attachment
from app.models.incident import Incident

class IncidentRepository (RepositoryABC):
    """Saves and reads the incidents (and their attachment) in the database.

    Args:
        RepositoryABC (class): It inherits the methods of the parent class
    """

    def _row_to_incident(self,row: dict) -> Incident:
        """Turns a database row into an Incident.

        Args:
            row (dict): The row of the incident table, joined with the names of the user, analyst,
                severity and state

        Returns:
            Incident: The incident built from the row
        """
        # analyst_id is NULL while the ticket has no assigned analyst.
        analyst_id = row["analyst_id"]
        return Incident(
            id=UUID(str(row["id"])),
            user_id=UUID(str(row["user_id"])),
            analyst_id=UUID(str(analyst_id)) if analyst_id else None,
            user_name=row.get("user_name"),
            analyst_name=row.get("analyst_name"),
            source_url=row.get("source_url"),
            source_title=row.get("source_title"),
            title=row["title"],
            description=row["description"],
            severity=row["severity_id"],
            state=row["state_id"],
            open_date=row["open_date"],
            close_date=row["close_date"],
        )

    def create(self, incident: Incident):
        """Saves an incident in the database. If it has an attachment, it is saved too.

        Args:
            incident (Incident): The incident to save

        Returns:
            incident (Incident): The incident saved
        """
        query = (
            "INSERT INTO incident (id, user_id, title, description, severity_id, state_id, open_date, close_date, "
            "analyst_id, source_url, source_title) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    incident.id, incident.user_id, incident.title, incident.description,
                    incident.severity, incident.state,
                    incident.open_date, incident.close_date,
                    # analyst_id can be None (not assigned yet), and the database accepts it as NULL.
                    incident.analyst_id,
                    incident.source_url, incident.source_title,
                ))
                # The attachment goes in the same transaction: either both rows are saved or none.
                if incident.attachment:
                    attachment = incident.attachment
                    cursor.execute(
                        "INSERT INTO attachment (id, incident_id, filename, filetype, filesize, stored_name) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (attachment.id, incident.id, attachment.filename,
                         attachment.filetype, attachment.filesize, attachment.stored_name),
                    )
            self.db_connection.commit()
            return incident
        except MySQLError as e:
            print(f"Error inserting incident: {e}")
            self.db_connection.rollback()
            raise

    def get_all(self):
        """Gets all the incidents from the database.

        Returns:
            incidents (List): All the incidents
        """
        query = (
            "SELECT i.id, i.user_id, i.analyst_id, i.title, i.description, i.severity_id, s.name AS severity_name, "
            "i.state_id, st.name AS state_name, i.open_date, i.close_date, u.name AS user_name, "
            "u.email AS user_email, a.name AS analyst_name, a.email AS analyst_email, "
            "i.source_url, i.source_title "
            "FROM incident i INNER JOIN user u ON u.id = i.user_id LEFT JOIN user a ON a.id = i.analyst_id "
            "INNER JOIN con_severity s ON s.id = i.severity_id INNER JOIN con_state st ON st.id = i.state_id "
            "ORDER BY i.open_date DESC"
        )
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        incidents = []
        for result in results:
            one_incident = self._row_to_incident(result)
            incidents.append(one_incident)
        return incidents

    def get_by_id(self, incident_id: UUID):
        """Gets one incident by its UUID, with its attachment.

        Args:
            incident_id (UUID): The UUID of the incident

        Returns:
            incident (Incident): The incident, or None if it does not exist
        """
        query = (
            "SELECT i.id, i.user_id, i.analyst_id, i.title, i.description, i.severity_id, s.name AS severity_name, "
            "i.state_id, st.name AS state_name, i.open_date, i.close_date, u.name AS user_name, "
            "u.email AS user_email, a.name AS analyst_name, a.email AS analyst_email, "
            "i.source_url, i.source_title "
            "FROM incident i INNER JOIN user u ON u.id = i.user_id LEFT JOIN user a ON a.id = i.analyst_id "
            "INNER JOIN con_severity s ON s.id = i.severity_id INNER JOIN con_state st ON st.id = i.state_id "
            "WHERE i.id = %s"
        )
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (incident_id,))
            result = cursor.fetchone()
        if result is None:
            return None

        incident = self._row_to_incident(result)
        incident.attachment = self._get_attachment(incident.id)
        return incident

    def _get_attachment(self, incident_id: UUID):
        """Gets the attachment of an incident.

        Args:
            incident_id (UUID): The UUID of the incident

        Returns:
            attachment (Attachment): The attachment, or None if the incident has no file
        """
        query = (
            "SELECT id, incident_id, filename, filetype, filesize, stored_name "
            "FROM attachment WHERE incident_id = %s"
        )
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (incident_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return Attachment(
            id=UUID(str(row["id"])),
            incident_id=UUID(str(row["incident_id"])),
            filename=row["filename"],
            filetype=row["filetype"],
            filesize=row["filesize"],
            stored_name=row["stored_name"],
        )

    def get_by_user(self, user_id: UUID):
        """Gets all the incidents created by a user.

        Args:
            user_id (UUID): The UUID of the user who created the incidents

        Returns:
            incidents (List): The incidents of that user, from newest to oldest
        """
        query = (
            "SELECT i.id, i.user_id, i.analyst_id, i.title, i.description, i.severity_id, s.name AS severity_name, "
            "i.state_id, st.name AS state_name, i.open_date, i.close_date, u.name AS user_name, "
            "u.email AS user_email, a.name AS analyst_name, a.email AS analyst_email, "
            "i.source_url, i.source_title "
            "FROM incident i INNER JOIN user u ON u.id = i.user_id LEFT JOIN user a ON a.id = i.analyst_id "
            "INNER JOIN con_severity s ON s.id = i.severity_id INNER JOIN con_state st ON st.id = i.state_id "
            "WHERE i.user_id = %s ORDER BY i.open_date DESC"
        )
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
        return [self._row_to_incident(result) for result in results]

    def update(self, id: UUID, incident: Incident):
        """Updates the severity, state, analyst and close date of an incident.

        Args:
            id (UUID): The UUID of the incident to update
            incident (Incident): The incident with the new values

        Returns:
            incident (Incident): The incident updated
        """
        query = (
            "UPDATE incident SET severity_id = %s, state_id = %s, analyst_id = %s, close_date = %s WHERE id = %s"
        )
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    incident.severity, incident.state,
                    incident.analyst_id, incident.close_date,
                    id,
                ))
            self.db_connection.commit()
            return incident
        except MySQLError as e:
            print(f"Error editing incident: {e}")
            self.db_connection.rollback()
            raise

    def delete(self, id: UUID):
        """Deletes an incident.

        Args:
            id (UUID): The UUID of the incident to delete

        Returns:
            deleted (bool): True if the incident was deleted, False if it did not exist
        """
        query = "DELETE FROM incident WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (id,))
                # rowcount = deleted rows
                deleted = cursor.rowcount > 0
            self.db_connection.commit()
            return deleted
        except MySQLError as e:
            print(f"Error deleting incident: {e}")
            self.db_connection.rollback()
            raise
