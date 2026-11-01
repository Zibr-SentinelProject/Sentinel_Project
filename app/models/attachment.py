import os
from uuid import UUID, uuid4

class Attachment():

    PATHFILE = "attachments/"

    def __init__(self, incident_id: UUID, filename: str, filetype: str, filesize: int, id: UUID = None,
                 path: str = None):
        self.id = id or uuid4()
        self.incident_id = incident_id
        self.filename = filename
        self.filetype = filetype
        self.filesize = filesize
        # The file on disk uses the (unique) id and keeps the extension; the original name is only displayed.
        # A path read from the DB is kept as it is, because old attachments don't follow the <id>.<ext> format.
        extension = os.path.splitext(filename)[1]
        self._path = path or self.PATHFILE + f"{self.id}{extension}"

    @property
    def path(self) -> str:
        return self._path

    def save_file(self, content: bytes):
        """Writes the content to disk."""
        os.makedirs(self.PATHFILE, exist_ok=True)
        # "xb": fails if the file already exists, so another attachment is never overwritten.
        with open(self.path, "xb") as file:
            file.write(content)

    def remove_file(self):
        """Deletes the file from disk. If it is already gone, there is nothing to clean up."""
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass

    def __repr__(self):
        return f"<Attachment(filename={self.filename}, filetype={self.filetype}, filesize={self.filesize})>"
