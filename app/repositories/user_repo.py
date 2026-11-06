from uuid import UUID
from pymysql import MySQLError
from pymysql.cursors import DictCursor
from app.repositories.abc_repo import RepositoryABC
from app.models.user import User, ROLE_CLASSES

class UserRepository(RepositoryABC):
    """Saves and reads the users (analysts and employees) in the database."""

    def _row_to_user(self,row: dict) -> User:
        """Turns a database row into an Analyst or an Employee.

        Args:
            row (dict): The row of the user table

        Returns:
            User: An Analyst or an Employee, depending on the role of the row
        """
        # The role column decides whether we return an Analyst or an Employee.
        user_class = ROLE_CLASSES[row["role"]]
        return user_class(
            id=UUID(str(row["id"])),
            name=str(row["name"]),
            email=str(row["email"]),
            password=str(row["password"])
        )

    def get_all(self):
        """Gets all the users from the database.

        Returns:
            users (List): All the users, ordered by name
        """
        query = "SELECT id, name, email, password, role FROM user ORDER BY name"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        users = []
        for result in results:
            one_user = self._row_to_user(result)
            users.append(one_user)
        return users

    def get_by_id(self, user_id: UUID):
        """Gets one user by its UUID.

        Args:
            user_id (UUID): The UUID of the user

        Returns:
            user (User): The user, or None if it does not exist
        """
        query = "SELECT id, name, email, password, role FROM user WHERE id = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
        return self._row_to_user(result) if result else None

    def get_by_email(self, email: str):
        """Gets one user by its email. It is used to log in and to check that an email is not repeated.

        Args:
            email (str): The email of the user

        Returns:
            user (User): The user, or None if no one has that email
        """
        query = "SELECT id, name, email, password, role FROM user WHERE email = %s"
        with self.db_connection.cursor(DictCursor) as cursor:
            cursor.execute(query, (email,))
            result = cursor.fetchone()
        return self._row_to_user(result) if result else None

    def create(self, new_user: User):
        """Saves a user in the database, with its role.

        Args:
            new_user (User): The user to save

        Returns:
            user (User): The user saved
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

    def update(self, id: UUID, updated_user: User):
        """Updates the name, email and password of a user. The role is changed with update_role.

        Args:
            id (UUID): The UUID of the user to update
            updated_user (User): The user with the new values

        Returns:
            user (User): The user updated
        """
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

    def update_role(self, id: UUID, role: str):
        """Changes the role of a user.

        Args:
            id (UUID): The UUID of the user
            role (str): The new role (ANALYST or EMPLOYEE)
        """
        query = "UPDATE user SET role = %s WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (role, id))
            self.db_connection.commit()
        except MySQLError as e:
            print(f"Error updating role: {e}")
            self.db_connection.rollback()
            raise

    def delete(self, id: UUID):
        """Deletes a user.

        Args:
            id (UUID): The UUID of the user to delete

        Returns:
            deleted (bool): True if the user was deleted, False if it did not exist
        """
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
