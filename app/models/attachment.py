from pathlib import Path
from uuid import UUID, uuid4

class Attachment():

    # Folder where the files are saved. Only this line knows it: the DB stores just the file name.
    PATHFILE = Path("attachments")

    def __init__(self, incident_id: UUID, filename: str, filetype: str, filesize: int, id: UUID = None,
                 stored_name: str = None):
        self.id = id or uuid4()
        self.incident_id = incident_id
        self.filename = filename
        self.filetype = filetype
        self.filesize = filesize
        # Name of the file inside PATHFILE: the (unique) id plus the extension. The original name is only displayed.
        self.stored_name = stored_name or f"{self.id}{Path(filename).suffix}"

    @property
    def path(self) -> Path:
        """Full path of the file, built from PATHFILE every time it is needed."""
        return self.PATHFILE / self.stored_name

    def save_file(self, content: bytes):
        """Writes the content to disk."""
        self.PATHFILE.mkdir(parents=True, exist_ok=True)
        # "xb": fails if the file already exists, so another attachment is never overwritten.
        with self.path.open("xb") as file:
            file.write(content)

    def remove_file(self):
        """Deletes the file from disk. If it is already gone, there is nothing to clean up."""
        self.path.unlink(missing_ok=True)

    def __repr__(self):
        return f"<Attachment(filename={self.filename}, filetype={self.filetype}, filesize={self.filesize})>"
