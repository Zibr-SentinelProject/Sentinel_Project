from uuid import UUID

from pymysql import MySQLError
from pymysql.cursors import DictCursor

from app.repositories.abc_repo import RepositoryABC
from app.models.incident import Incident

class IncidentRepository (RepositoryABC):

    def create(self, incident: Incident):
        query = (
            "INSERT INTO incident (id, user_id, title, description, severity, state, open_date, close_date, "
            "analyst_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    incident.id, incident.user_id, incident.title, incident.description,
                    incident.severity, incident.state,
                    incident.open_date, incident.close_date,
                    # analyst_id puede ser None (todavía sin asignar), y la base de datos lo acepta como NULL.
                    incident.analyst_id,
                ))
            self.db_connection.commit()
            return incident
        except MySQLError as e:
            print(f"Error inserting incident: {e}")
            self.db_connection.rollback()
            raise

    def get_all(self):
        query = "SELECT i.id, i.user_id, i.analyst_id, i.title, i.description, i.severity_id, s.name AS severity_name, i.state_id, st.name AS state_name, i.open_date, i.close_date, u.name AS user_name, u.email AS user_email, a.name AS analyst_name, a.email AS analyst_email FROM incident i INNER JOIN user u ON u.id = i.user_id LEFT JOIN user a ON a.id = i.analyst_id INNER JOIN con_severity s ON s.id = i.severity_id INNER JOIN con_state st ON st.id = i.state_id ORDER BY i.open_date DESC"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        incidents = []
        for result in results:
            one_user = self._row_to_user(result)
            incidents.append(one_user)
        return incidents

    def get_by_id(self, user_id: UUID):
        query = "SELECT i.id, i.user_id, i.analyst_id, i.title, i.description, i.severity_id, s.name AS severity_name, i.state_id, st.name AS state_name, i.open_date, i.close_date, u.name AS user_name, u.email AS user_email, a.name AS analyst_name, a.email AS analyst_email FROM incident i INNER JOIN user u ON u.id = i.user_id LEFT JOIN user a ON a.id = i.analyst_id INNER JOIN con_severity s ON s.id = i.severity_id INNER JOIN con_state st ON st.id = i.state_id WHERE i.id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
        return self._row_to_user(result) if result else None

    def update(self, id: UUID, incident: Incident):
        query = "UPDATE incident SET severity = %s, state = %s, analyst_id = %s WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    incident.severity, incident.state,
                    incident.analyst_id,
                    id,
                ))
            self.db_connection.commit()
            return incident
        except MySQLError as e:
            print(f"Error editing incident: {e}")
            self.db_connection.rollback()
            raise

    # ID necesita la coma para ser tupla: (id,),
    # y delete devuelve True si borró el incidente o False si no existía
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
                # rowcount = filas borradas
                deleted = cursor.rowcount > 0
            self.db_connection.commit()
            return deleted
        except MySQLError as e:
            print(f"Error deleting incident: {e}")
            self.db_connection.rollback()
            raise
