from uuid import UUID
from pymysql import MySQLError
from pymysql.cursors import DictCursor
from app.repositories.abc_repo import RepositoryABC
from app.models.user import User

class UserRepository(RepositoryABC):

    def _row_to_user(self,row: dict) -> User:

        return User(
            id=UUID(str(row["id"])),
            name=str(row["name"]),
            email=str(row["email"]),
            password=str(row["password"])
        )

    # Antes usaba fetchone, ahora usa DictCursor, lee todas las filas (fetchall) dentro del with y devuelve una lista.
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
        query = "SELECT id, name, email, password FROM user"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        users = []
        for result in results:
            one_user = self._row_to_user(result)
            users.append(one_user)
        return users

    def get_by_id(self, user_id: UUID):
        #Le quité un =
        # query = "SELECT id, name, email, password FROM user WHERE id == %s"
        query = "SELECT id, name, email, password FROM user WHERE id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
        return self._row_to_user(result) if result else None

    # Cambié el nombre del parametro a "new_user".
    # Saqué el commit y el return del with.
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
        query = "INSERT INTO user (id, name, email, password) VALUES (%s, %s, %s, %s)"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    new_user.id, str(new_user.name), str(new_user.email), str(new_user.password)
                ))
            self.db_connection.commit()
            return new_user
        except MySQLError as e:
            print(f"Error inserting user: {e}")
            self.db_connection.rollback()
            raise

    # Cambie execute() por cursor, quité un = y faltaba el commit. Además update recibe (id, entity),
    # igual que la clase RepositoryABC.
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
                    #No necesitas convertirlo a str, porque ya son str, no rompe nada, pero por si lo quieres quitar
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

    # Daba error, se necesitaba la coma: (id,).
    # Ahora devuelve True si borró el usuario o False si no existía.
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
                # rowcount = filas borradas; se lee dentro del with, antes de que se cierre el cursor.
                deleted = cursor.rowcount > 0
            self.db_connection.commit()
            return deleted
        except MySQLError as e:
            print(f"Error deleting user: {e}")
            self.db_connection.rollback()
            raise
