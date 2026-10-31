from uuid import UUID

from flask import Blueprint, jsonify, render_template, session

from app.db.database import check_connection, get_db
from app.repositories.attachment_repo import AttachmentRepository
from app.repositories.comment_repo import CommentRepository
from app.repositories.incident_repo import IncidentRepository
from app.repositories.user_repo import UserRepository
from app.services.attachment_service import AttachmentService
from app.services.comment_service import CommentService
from app.services.incident_service import IncidentService
from app.services.user_service import UserService

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/health")
def health():
    connected, detail = check_connection()
    body = {"status": "ok" if connected else "error", "database": detail}
    return jsonify(body), 200 if connected else 503


def current_user():
    """Return the session user, or None if nobody is logged in."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    try:
        return UserService(UserRepository(get_db())).get_user(UUID(user_id))
    except LookupError:
        # The session user no longer exists in the database.
        session.clear()
        return None


def get_comment_service():
    """CommentService needs the IncidentService to check who can view each ticket."""
    incident_service = IncidentService(IncidentRepository(get_db()))
    return CommentService(CommentRepository(get_db()), incident_service)


def get_attachment_service():
    incident_service = IncidentService(IncidentRepository(get_db()))
    return AttachmentService(AttachmentRepository(get_db()), incident_service)


def login_error():
    return jsonify(error="Login required"), 401


def register_error_handlers(app):
    """Services raise exceptions; here we turn them into HTTP responses for the whole app."""

    @app.errorhandler(PermissionError)
    def forbidden(error):
        return jsonify(error=str(error)), 403

    @app.errorhandler(LookupError)
    def not_found(error):
        return jsonify(error=str(error)), 404

    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify(error=str(error)), 400
