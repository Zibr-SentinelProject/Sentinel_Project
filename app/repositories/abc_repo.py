class RepositoryABC:

    def __init__(self, db_connection):
        self.db_connection = db_connection

    def get_all(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def get_by_id(self, id):
        raise NotImplementedError("Subclasses must implement this method.")

    def create(self, entity):
        raise NotImplementedError("Subclasses must implement this method.")

    def update(self, id, entity):
        raise NotImplementedError("Subclasses must implement this method.")

    def delete(self, id):
        raise NotImplementedError("Subclasses must implement this method.")