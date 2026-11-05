from uuid import UUID
from pymysql import MySQLError
from pymysql.cursors import DictCursor
from app.repositories.abc_repo import RepositoryABC
from app.models.user import User, ROLE_CLASSES

class UserRepository(RepositoryABC):

    def _row_to_user(self,row: dict) -> User:
        """This function Turns a sql row into an object User.

        Args:
            row (sqlrow): This is the sql row that gives the database.

        Returns:
            User (class): Ibject User.
        """
        # La columna role decide si devolvemos un Analyst o un Employee.
        user_class = ROLE_CLASSES[row["role"]]
        return user_class(
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
        """This function makes a query to get all the users from the data base and makes them objects User.

        Returns:
            User (class): Object User.
        """
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
        """This Function makes a query to get the users from the database that have the specified id.

        Args:
            user_id (UUID): is the user id

        Returns:
            User (class): Object User.
        """
        #Le quité un =
        # query = "SELECT id, name, email, password FROM user WHERE id == %s"
        query = "SELECT id, name, email, password, role FROM user WHERE id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
        return self._row_to_user(result) if result else None

    def get_by_email(self, email: str):
        """this function gets a user by their email.

        Args:
            email (str): user email

        Returns:
            User: it returns a user if there's a user with that email, if not, it returns none. 
        """
        query = "SELECT id, name, email, password, role FROM user WHERE email = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (email,))
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
        """This function creates a new user object and a new row in the data base with the parametters given.

        Args:
            new_user (parametters): This are the parametters to the new User (id, name, email, password, role).

        Returns:
            User (Class): Object User.
        """
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
        """This function updates a user with the id given with the parametters given.

        Args:
            id (UUID): The user id.
            updated_user (parametters): the new user parametters

        Returns:
            User (class): Object User.
        """
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
        """This function deletes the user with the given id.

        Args:
            id (UUID): The user id.

        Returns:
            str: it returns deleted if the user was succesfully deleted or the database error if not.
        """
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
