from uuid import UUID
import pymysql.cursors
from pymysql import MySQLError
from app.repositories.abc_repo import RepositoryABC
from app.models.user import user

class user_repo(RepositoryABC):

    def _row_to_user(self,row: dict) -> user:

        return user(
            id=UUID(str(row["id"])),
            name=str(row["name"]),
            email=str(row["email"]),
            password=str(row["password"])
        )

    def get_all(self):
        query = "SELECT id, name, email, password FROM user"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query)
            result = cursor.fetchone()
            return self._row_to_user(result) if result else None
        except MySQLError as e:
            print(f"Error getting all users: {e}")
            self.db_connection.rollback()
            raise

    def get_by_id(self, user_id: UUID):
        query = "SELECT id, name, email, password FROM user WHERE id == %s"
        with self.db_connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, (str(user_id),))
            result = cursor.fetchone()
        return self._row_to_user(result) if result else None

    def create(self, user: user):
        query = "INSERT INTO user (id, name, email, password) VALUES (%s, %s, %s, %s)"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    str(user.id), str(user.name), str(user.email), str(user.password)
                ))
                self.db_connection.commit()
                return user
        except MySQLError as e:
            print(f"Error inserting user: {e}")
            self.db_connection.rollback()
            raise

    def update(self, user: user):
        query = "UPDATE user SET (name = %s, email = %s, password = %s) WHERE id == %s"
        try:
            with self.db_connection.execute(query, (
                    str(user.name),
                    str(user.email),
                    str(user.password),
                    str(user.id)
                )):
                return user
        except MySQLError as e:
            print(f"Error updating user: {e}")
            self.db_connection.rollback()
            raise

    def delete(self, id):
        query = "DELETE FROM user WHERE id == %s"
        try:
            with self.db_connection.execute(query, (
                str(id)
            )):
                return None
        except MySQLError as e:
            print(f"Error deleting user: {e}")
            self.db_connection.rollback()
            raise

