from abc import ABC, abstractmethod


class RepositoryABC(ABC):

    def __init__(self, db_connection):
        self.db_connection = db_connection

    def get_all(self):
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def get_by_id(self, id):
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def create(self, entity):
        raise NotImplementedError("Subclasses must implement this method.")

#TODO Check if the update with passing the id
    @abstractmethod
    def update(self, id, entity):
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def delete(self, id):
        raise NotImplementedError("Subclasses must implement this method.")
