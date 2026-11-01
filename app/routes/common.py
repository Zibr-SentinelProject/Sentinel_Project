from uuid import UUID

from flask import Blueprint, jsonify, render_template, session

from app.services.factory import get_user_service

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


def current_user():
    """Return the session user, or None if nobody is logged in."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    try:
        return get_user_service().get_user(UUID(user_id))
    except LookupError:
        # The session user no longer exists in the database.
        session.clear()
        return None


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
