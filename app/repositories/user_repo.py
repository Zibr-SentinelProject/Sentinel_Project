from uuid import UUID
from pymysql import MySQLError
from pymysql.cursors import DictCursor
from app.repositories.abc_repo import RepositoryABC
from app.models.user import User, ROLE_CLASSES

class UserRepository(RepositoryABC):

    def _row_to_user(self,row: dict) -> User:
        # The role column decides whether we return an Analyst or an Employee.
        user_class = ROLE_CLASSES[row["role"]]
        return user_class(
            id=UUID(str(row["id"])),
            name=str(row["name"]),
            email=str(row["email"]),
            password=str(row["password"])
        )

    # It used fetchone before; now it uses DictCursor, reads all the rows (fetchall) inside the with and returns a list.
    # def get_all(self):
    #     query = "SELECT id, name, email, password FROM user"
    #     try:
    #         with self.db_connection.cursor() as cursor:
    #             cursor.execute(query)
    #         result = cursor.fetchone()
    #         return self._row_to_user(result) if result else None
    #     except MySQLError as e:
    #         print(f"Error getting all users: {e}")
    #         self.db_connection.rollback()
    #         raise
    def get_all(self):
        query = "SELECT id, name, email, password, role FROM user"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        users = []
        for result in results:
            one_user = self._row_to_user(result)
            users.append(one_user)
        return users

    def get_by_id(self, user_id: UUID):
        # I removed a =
        # query = "SELECT id, name, email, password FROM user WHERE id == %s"
        query = "SELECT id, name, email, password, role FROM user WHERE id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
        return self._row_to_user(result) if result else None

    def get_by_email(self, email: str):
        query = "SELECT id, name, email, password, role FROM user WHERE email = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (email,))
            result = cursor.fetchone()
        return self._row_to_user(result) if result else None

    # I renamed the parameter to "new_user".
    # I moved the commit and the return out of the with.
    # def create(self, user: user):
    #     query = "INSERT INTO user (id, name, email, password) VALUES (%s, %s, %s, %s)"
    #     try:
    #         with self.db_connection.cursor() as cursor:
    #             cursor.execute(query, (
    #                 str(user.id), str(user.name), str(user.email), str(user.password)
    #             ))
    #             self.db_connection.commit()
    #             return user
    #     except MySQLError as e:
    #         print(f"Error inserting user: {e}")
    #         self.db_connection.rollback()
    #         raise
    def create(self, new_user: User):
        query = "INSERT INTO user (id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    new_user.id, str(new_user.name), str(new_user.email), str(new_user.password), new_user.ROLE
                ))
            self.db_connection.commit()
            return new_user
        except MySQLError as e:
            print(f"Error inserting user: {e}")
            self.db_connection.rollback()
            raise

    # I replaced execute() with cursor, removed a = and the commit was missing. Also update receives (id, entity),
    # like the RepositoryABC class.
    # def update(self, user: user):
    #     query = "UPDATE user SET (name = %s, email = %s, password = %s) WHERE id == %s"
    #     try:
    #         with self.db_connection.execute(query, (
    #                 str(user.name),
    #                 str(user.email),
    #                 str(user.password),
    #                 str(user.id)
    #             )):
    #             return user
    #     except MySQLError as e:
    #         print(f"Error updating user: {e}")
    #         self.db_connection.rollback()
    #         raise
    def update(self, id: UUID, updated_user: User):
        query = "UPDATE user SET name = %s, email = %s, password = %s WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    # You don't need to convert it to str, since they are already str;
                    # it breaks nothing, but in case you want to remove it
                    str(updated_user.name),
                    str(updated_user.email),
                    str(updated_user.password),
                    id,
                ))
            self.db_connection.commit()
            return updated_user
        except MySQLError as e:
            print(f"Error updating user: {e}")
            self.db_connection.rollback()
            raise

    # It raised an error, the comma was needed: (id,).
    # Now it returns True if the user was deleted or False if it did not exist.
    # def delete(self, id):
    #     query = "DELETE FROM user WHERE id == %s"
    #     try:
    #         with self.db_connection.execute(query, (
    #             str(id)
    #         )):
    #             return None
    #     except MySQLError as e:
    #         print(f"Error deleting user: {e}")
    #         self.db_connection.rollback()
    #         raise
    def delete(self, id: UUID):
        query = "DELETE FROM user WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (id,))
                # rowcount = deleted rows; read inside the with, before the cursor is closed.
                deleted = cursor.rowcount > 0
            self.db_connection.commit()
            return deleted
        except MySQLError as e:
            print(f"Error deleting user: {e}")
            self.db_connection.rollback()
            raise
