import os
from pathlib import Path
from uuid import UUID, uuid4

class Attachment():
    """A file attached to an incident."""

    # Folder where the files are saved; None means "use ATTACHMENTS_DIR from the .env, or attachments/ in the project
    # root". Only folder() knows it: the DB stores just the file name.
    PATHFILE = None

    def __init__(self, incident_id: UUID, filename: str, filetype: str, filesize: int, id: UUID = None,
                 stored_name: str = None):
        """Creates an attachment.

        Args:
            incident_id (UUID): The incident the file belongs to
            filename (str): The original name of the file (only shown to the user)
            filetype (str): The type of the file
            filesize (int): The size of the file
            id (UUID, optional): Only used when the attachment comes from the database. Defaults to None.
            stored_name (str, optional): Only used when the attachment comes from the database. Defaults to None.
        """
        self.id = id or uuid4()
        self.incident_id = incident_id
        self.filename = filename
        self.filetype = filetype
        self.filesize = filesize
        # Name of the file inside PATHFILE: the (unique) id plus the extension. The original name is only displayed.
        self.stored_name = stored_name or f"{self.id}{Path(filename).suffix}"

    @classmethod
    def folder(cls) -> Path:
        """Gets the folder where the files are saved.

        Returns:
            folder (Path): The full path of the folder
        """
        # Absolute because a relative path depends on the working directory, which under Apache is "/".
        return cls.PATHFILE or Path(os.getenv("ATTACHMENTS_DIR") or Path(__file__).resolve().parents[2] / "attachments")

    @property
    def path(self) -> Path:
        """Gets the full path of the file.

        Returns:
            path (Path): The folder plus the name of the file
        """
        return self.folder() / self.stored_name

    def save_file(self, content: bytes):
        """Saves the file on disk. It creates the folder if it does not exist.

        Args:
            content (bytes): The content of the file

        Raises:
            FileExistsError: If a file with that name already exists
        """
        self.folder().mkdir(parents=True, exist_ok=True)
        # "xb": fails if the file already exists, so another attachment is never overwritten.
        with self.path.open("xb") as file:
            file.write(content)

    def remove_file(self):
        """Deletes the file from disk. If it is already gone, nothing happens."""
        self.path.unlink(missing_ok=True)

    def __repr__(self):
        return f"<Attachment(filename={self.filename}, filetype={self.filetype}, filesize={self.filesize})>"
