from app.db.database import get_db
from app.repositories.attachment_repo import AttachmentRepository
from app.repositories.comment_repo import CommentRepository
from app.repositories.incident_repo import IncidentRepository
from app.repositories.user_repo import UserRepository
from app.services.attachment_service import AttachmentService
from app.services.comment_service import CommentService
from app.services.incident_service import IncidentService
from app.services.user_service import UserService


# The routes get their services from here. Only this file connects services with the database.

def get_user_service():
    return UserService(UserRepository(get_db()))


def get_incident_service():
    return IncidentService(IncidentRepository(get_db()))


def get_comment_service():
    """CommentService needs the IncidentService to check who can view each ticket."""
    return CommentService(CommentRepository(get_db()), get_incident_service())


def get_attachment_service():
    return AttachmentService(AttachmentRepository(get_db()), get_incident_service())

