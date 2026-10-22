from uuid import UUID

import pymysql.cursors

from app.repositories.abc_repo import RepositoryABC
from app.models.incident import incident

class incidentRepository (RepositoryABC):

    def create(self, incident: incident):
        query = "INSERT INTO INSERT (id, user_id, title, description, severity, state, open_date, close_date, analyst_id)" \
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    incident.id, incident.user_id, incident.title, incident.description, incident.severity, incident.state, 
                    incident.open_date, incident.close_date, incident.analyst_id
                ))
            self.db_connection.commit()
            return incident
        except pymysql.MySQLError as e:
            print(f"Error inserting incident: {e}")
            self.db_connection.rollback()
            raise

    def update(self, id: UUID, incident: incident):
        query = "UPDATE incident SET (severity = %s, state = %s, analyst_id = %s) WHERE id=%s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    incident.severity, incident.state, incident.analyst_id, id
                ))
            self.db_connection.commit()
            return incident
        except pymysql.MySQLError as e:
            print(f"Error editing incident: {e}")
            self.db_connection.rollback()
            raise

    def delete(self, id: UUID):
        query = "DELETE FROM incident WERE id=%s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    id
                ))
            self.db_connection.commit()
            return incident
        except pymysql.MySQLError as e:
            print(f"Error deleting incident: {e}")
            self.db_connection.rollback()
            raise