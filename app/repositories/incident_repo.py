from uuid import UUID

import pymysql.cursors

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
        except pymysql.MySQLError as e:
            print(f"Error inserting incident: {e}")
            self.db_connection.rollback()
            raise

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
        except pymysql.MySQLError as e:
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
        except pymysql.MySQLError as e:
            print(f"Error deleting incident: {e}")
            self.db_connection.rollback()
            raise
