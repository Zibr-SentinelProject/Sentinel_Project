from uuid import UUID

from pymysql import MySQLError
from pymysql.cursors import DictCursor

from app.repositories.abc_repo import RepositoryABC
from app.models.incident import Incident

class IncidentRepository (RepositoryABC):
    """This class is used to comunicate between the database and the web

    Args:
        RepositoryABC (class): It inherits the methods of the parent class
    """

    def _row_to_incident(self,row: dict) -> Incident:
        """This method coverts a database query into a python object

        Args:
            row (dict): It recibes row of the incident table of the database

        Returns:
            Incident: It return an incident object with the information of the row
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
        """This method is used to add rows of incidents into de database

        Args:
            incident (Incident): It recibes an incident object to insert it

        Returns:
            incident (Incident): It resturns an incident when the insertion was successful
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
            self.db_connection.commit()
            return incident
        except MySQLError as e:
            print(f"Error inserting incident: {e}")
            self.db_connection.rollback()
            raise

    def get_all(self):
        """This method is used to get all of incidents from de database

        Returns:
            incidents (List): this method returns a list whith all of the incidents on the database
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
        """This method is used to get one incident from de database

        Args:
            incident_id (UUID): It recibes an incident UUID

        Returns:
            incident (Incident): It retuns an incident when the select was successful
            none: It return none when the select fails or returns nothing
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
        return self._row_to_incident(result) if result else None

    def get_by_user(self, user_id: UUID):
        """This method is used to get all the incidents of a user

        Args:
            user_id (UUID): Id of the user who created the tickets

        Returns:
            incidents (List): the tickets created by that user, from newest to oldest
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

    # The id needs the comma to be a tuple: (id,),
    # and delete returns True if the incident was deleted or False if it did not exist
    # def delete(self, id: UUID):
    #     query = "DELETE FROM incident WERE id=%s"
    #     try:
    #         with self.db_connection.cursor() as cursor:
    #             cursor.execute(query, (
    #                 id
    #             ))
    #         self.db_connection.commit()
    #         return incident
    #     except pymysql.MySQLError as e:
    #         print(f"Error deleting incident: {e}")
    #         self.db_connection.rollback()
    #         raise
    def delete(self, id: UUID):
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
