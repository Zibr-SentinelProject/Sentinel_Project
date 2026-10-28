import os
from uuid import UUID

from app.models.attachement import Attachment
from app.models.user import User


class AttachmentService:

    def __init__(self, attachment_repo, incident_service):
        self.attachment_repo = attachment_repo
        self.incident_service = incident_service

    def add_attachment(self, user: User, incident_id: UUID, filename: str, filetype: str, content: bytes):
        """Adjuntan el creador del ticket y el analista asignado. Valida y guarda el archivo en disco."""
        incident = self.incident_service.find_incident(incident_id)
        if not self.incident_service.can_participate(user, incident):
            raise PermissionError("You cannot attach files to this incident")

        # basename evita nombres con rutas como "../x" al escribir en disco.
        attachment = Attachment(incident.id, os.path.basename(filename), filetype, len(content))
        if not attachment.is_valid_filetype():
            raise ValueError("File type not allowed")
        if not attachment.is_valid_filesize():
            raise ValueError("File is too big")

        os.makedirs(Attachment.PATHFILE, exist_ok=True)
        # "xb": falla si el archivo ya existe, así nunca se sobrescribe otro adjunto.
        with open(attachment.full_path, "xb") as file:
            file.write(content)

        try:
            created_attachment = self.attachment_repo.create(attachment)
            return created_attachment
        except Exception:
            # Si no se pudo registrar en la BD, no dejamos el archivo huérfano.
            os.remove(attachment.full_path)
            raise

    def list_attachments(self, user: User, incident_id: UUID):
        """Los ve quien puede ver el ticket."""
        # get_incident ya comprueba que el usuario pueda ver el ticket.
        incident = self.incident_service.get_incident(user, incident_id)
        attachments = self.attachment_repo.get_all_by_incident(incident.id)
        return attachments
