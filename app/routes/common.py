from uuid import UUID

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session

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
    """Services raise exceptions; here we turn them into a flashed message for the whole app."""

    def back_with_error(error):
        # flash() keeps the message in the session; base.html shows it on the page we go back to.
        flash(str(error), "error")
        return redirect(request.referrer or "/incidents")

    @app.errorhandler(PermissionError)
    def forbidden(error):
        return back_with_error(error)

    @app.errorhandler(LookupError)
    def not_found(error):
        return back_with_error(error)

    @app.errorhandler(ValueError)
    def bad_request(error):
        return back_with_error(error)
