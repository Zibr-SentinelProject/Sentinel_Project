import os
from uuid import UUID

from app.models.attachment import Attachment
from app.models.user import User


class AttachmentService:

    def __init__(self, attachment_repo, incident_service):
        self.attachment_repo = attachment_repo
        self.incident_service = incident_service

    def add_attachment(self, user: User, incident_id: UUID, filename: str, filetype: str, content: bytes):
        """The ticket creator and the assigned analyst can attach files. Validates and saves the file to disk."""
        incident = self.incident_service.find_incident(incident_id)
        if not self.incident_service.can_participate(user, incident):
            raise PermissionError("You cannot attach files to this incident")
        # only one attachment per incident.
        if self.attachment_repo.get_all_by_incident(incident.id):
            raise ValueError("This incident already has an attachment")

        # basename avoids names with paths like "../x" when writing to disk.
        safe_filename = os.path.basename(filename)
        if not safe_filename:
            raise ValueError("Filename is required")

        attachment = Attachment(incident.id, safe_filename, filetype, len(content))
        if not attachment.is_valid_filetype():
            raise ValueError("File type not allowed")
        if not attachment.is_valid_filesize():
            raise ValueError("File is too big")

        os.makedirs(Attachment.PATHFILE, exist_ok=True)
        # "xb": fails if the file already exists, so another attachment is never overwritten.
        with open(attachment.path, "xb") as file:
            file.write(content)

        try:
            created_attachment = self.attachment_repo.create(attachment)
            return created_attachment
        except Exception:
            # If it could not be registered in the DB, we don't leave the file orphaned.
            os.remove(attachment.path)
            raise

    def list_attachments(self, user: User, incident_id: UUID):
        """Visible to whoever can view the ticket."""
        # get_incident already checks that the user can view the ticket.
        incident = self.incident_service.get_incident(user, incident_id)
        attachments = self.attachment_repo.get_all_by_incident(incident.id)
        return attachments

    def get_attachment(self, user: User, attachment_id: UUID):
        """Visible to whoever can view the ticket it belongs to."""
        attachment = self._find_attachment(attachment_id)
        # get_incident already checks that the user can view the ticket.
        self.incident_service.get_incident(user, attachment.incident_id)
        return attachment

    def delete_attachment(self, user: User, attachment_id: UUID):
        """The ticket creator and the assigned analyst can delete it. The record is deleted first, then the file."""
        attachment = self._find_attachment(attachment_id)
        incident = self.incident_service.find_incident(attachment.incident_id)
        if not self.incident_service.can_participate(user, incident):
            raise PermissionError("You cannot delete attachments from this incident")

        deleted = self.attachment_repo.delete(attachment.id)
        if deleted:
            try:
                os.remove(attachment.path)
            except FileNotFoundError:
                # The record no longer exists; if the file doesn't either, there is nothing to clean up.
                pass
        return deleted

    def _find_attachment(self, attachment_id: UUID):
        attachment = self.attachment_repo.get_by_id(attachment_id)
        if attachment is None:
            raise LookupError("Attachment not found")
        return attachment
