import os
from uuid import UUID

from app.models.attachment import Attachment
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
        safe_filename = os.path.basename(filename)
        if not safe_filename:
            raise ValueError("Filename is required")

        attachment = Attachment(incident.id, safe_filename, filetype, len(content))
        if not attachment.is_valid_filetype():
            raise ValueError("File type not allowed")
        if not attachment.is_valid_filesize():
            raise ValueError("File is too big")

        os.makedirs(Attachment.PATHFILE, exist_ok=True)
        # "xb": falla si el archivo ya existe, así nunca se sobrescribe otro adjunto.
        with open(attachment.path, "xb") as file:
            file.write(content)

        try:
            created_attachment = self.attachment_repo.create(attachment)
            return created_attachment
        except Exception:
            # Si no se pudo registrar en la BD, no dejamos el archivo huérfano.
            os.remove(attachment.path)
            raise

    def list_attachments(self, user: User, incident_id: UUID):
        """Los ve quien puede ver el ticket."""
        # get_incident ya comprueba que el usuario pueda ver el ticket.
        incident = self.incident_service.get_incident(user, incident_id)
        attachments = self.attachment_repo.get_all_by_incident(incident.id)
        return attachments

    def get_attachment(self, user: User, attachment_id: UUID):
        """Lo ve quien puede ver el ticket al que pertenece."""
        attachment = self._find_attachment(attachment_id)
        # get_incident ya comprueba que el usuario pueda ver el ticket.
        self.incident_service.get_incident(user, attachment.incident_id)
        return attachment

    def delete_attachment(self, user: User, attachment_id: UUID):
        """Lo borran el creador del ticket y el analista asignado. Primero borra el registro y luego el archivo."""
        attachment = self._find_attachment(attachment_id)
        incident = self.incident_service.find_incident(attachment.incident_id)
        if not self.incident_service.can_participate(user, incident):
            raise PermissionError("You cannot delete attachments from this incident")

        deleted = self.attachment_repo.delete(attachment.id)
        if deleted:
            try:
                os.remove(attachment.path)
            except FileNotFoundError:
                # El registro ya no existe; si el archivo tampoco, no hay nada que limpiar.
                pass
        return deleted

    def _find_attachment(self, attachment_id: UUID):
        attachment = self.attachment_repo.get_by_id(attachment_id)
        if attachment is None:
            raise LookupError("Attachment not found")
        return attachment
