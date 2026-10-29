from uuid import UUID

from app.models.comment import Comment
from app.models.user import User


class CommentService:

    def __init__(self, comment_repo, incident_service):
        self.comment_repo = comment_repo
        self.incident_service = incident_service

    def add_comment(self, user: User, incident_id: UUID, content: str):
        """Cualquier usuario logueado puede comentar en los tickets que creó."""
        incident = self.incident_service.find_incident(incident_id)
        if incident.user_id != user.id:
            raise PermissionError("You cannot comment on this incident")

        comment = Comment(content, user.id, incident.id)
        created_comment = self.comment_repo.create(comment)
        return created_comment

    def list_comments(self, user: User, incident_id: UUID):
        """Los ve quien puede ver el ticket."""
        # get_incident ya comprueba que el usuario pueda ver el ticket.
        incident = self.incident_service.get_incident(user, incident_id)
        comments = self.comment_repo.get_all_by_incident(incident.id)
        return comments
