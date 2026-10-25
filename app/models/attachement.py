from uuid import UUID, uuid4

class Attachment():

    MAX_FILE_SIZE_MB = 5
    PATHFILE = "attachments/"
    ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "application/pdf"]

    def __init__(self, incident_id: UUID, filename: str, filetype: str, filesize: int, id: UUID = None):
        self.id = id or uuid4()
        self.incident_id = incident_id
        self.filename = filename
        self.filetype = filetype
        self.filesize = filesize
        self.path = self.PATHFILE + filename

    def is_valid_filetype(self)-> bool:
        return self.filetype in self.ALLOWED_FILE_TYPES

    def is_valid_filesize(self) -> bool:
        return self.filesize <= self.MAX_FILE_SIZE_MB * 1024 * 1024

    def is_valid(self) -> bool:
        return self.is_valid_filetype() and self.is_valid_filesize()

    def __repr__(self):
        return f"<Attachment(filename={self.filename}, filetype={self.filetype}, filesize={self.filesize})>"
