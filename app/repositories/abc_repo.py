from abc import ABC, abstractmethod


class RepositoryABC(ABC):
    """Base class for all repositories. Defines the methods every repository must have."""

    def __init__(self, db_connection):
        """Creates the repository.

        Args:
            db_connection: The open connection to the database (see get_db)
        """
        self.db_connection = db_connection

    def get_all(self):
        """Gets all the entities. Subclasses should implement it."""
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def get_by_id(self, id):
        """Gets one entity by its id. Subclasses must implement it."""
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def create(self, entity):
        """Saves a new entity. Subclasses must implement it."""
        raise NotImplementedError("Subclasses must implement this method.")

#TODO Check if the update with passing the id
    @abstractmethod
    def update(self, id, entity):
        """Updates an existing entity. Subclasses must implement it."""
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def delete(self, id):
        """Deletes an entity by its id. Subclasses must implement it."""
        raise NotImplementedError("Subclasses must implement this method.")
