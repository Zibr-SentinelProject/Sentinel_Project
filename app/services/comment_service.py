from uuid import UUID

from app.models.comment import Comment
from app.models.user import User


class CommentService:
    """Rules for the comments of an incident."""

    def __init__(self, comment_repo, incident_service):
        """Creates the service.

        Args:
            comment_repo (CommentRepository): Used to save and read the comments
            incident_service (IncidentService): Used to check what the user can do with the incident
        """
        self.comment_repo = comment_repo
        self.incident_service = incident_service

    def add_comment(self, user: User, incident_id: UUID, content: str):
        """Adds a comment to an incident. Only the user who created it and the assigned analyst can comment.

        Args:
            user (User): The user who writes the comment
            incident_id (UUID): The incident to comment
            content (str): The text of the comment

        Raises:
            PermissionError: If the user cannot comment on the incident

        Returns:
            comment (Comment): The comment created
        """
        incident = self.incident_service.find_incident(incident_id)
        if not self.incident_service.can_participate(user, incident):
            raise PermissionError("You cannot comment on this incident")

        comment = Comment(content, user.id, incident.id)
        created_comment = self.comment_repo.create(comment)
        return created_comment

    def list_comments(self, user: User, incident_id: UUID):
        """Lists the comments of an incident. Anyone who can see the incident can see its comments.

        Args:
            user (User): The user who asks for the comments
            incident_id (UUID): The incident

        Returns:
            comments (List): The comments, from oldest to newest
        """
        # get_incident already checks that the user can view the ticket.
        incident = self.incident_service.get_incident(user, incident_id)
        comments = self.comment_repo.get_all_by_incident(incident.id)
        return comments
