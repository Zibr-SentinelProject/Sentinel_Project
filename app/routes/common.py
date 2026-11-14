from functools import wraps
from uuid import UUID

from flask import Blueprint, flash, redirect, render_template, request, session

from app.services.authorization import AccessDeniedError, require
from app.services.factory import get_user_service

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Shows the home page."""
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


def requires_permission(action):
    """Decorator for the routes that are about no object (e.g. /users): login first, then the permission.

    Without a login it goes to the login. Without permission, require raises AccessDeniedError (403).
    The view receives the logged-in user as its first argument, so it does not look it up again.

    Args:
        action (str): The action to check, one of the constants of app.services.authorization
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                return redirect("/login")
            require(user, action)
            return view(user, *args, **kwargs)
        return wrapper
    return decorator


def register_error_handlers(app):
    """Services raise exceptions; here we turn them into a flashed message for the whole app."""

    @app.errorhandler(AccessDeniedError)
    def access_denied(error):
        """A logged-in user is not allowed (AccessDeniedError): the error page itself, with the code chosen in require.

        It never redirects, so nothing from the request (like the Referer header) decides where the user goes.
        """
        message = "Not found" if error.status == 404 else "Forbidden"
        return render_template("error.html", status=error.status, message=message), error.status

    def back_with_error(error):
        """Shows the error message and goes back to the previous page (or to the incidents)."""
        # flash() keeps the message in the session; base.html shows it on the page we go back to.
        flash(str(error), "error")
        return redirect(request.referrer or "/incidents")

    @app.errorhandler(PermissionError)
    def forbidden(error):
        """The user is not allowed to do that (PermissionError)."""
        return back_with_error(error)

    @app.errorhandler(LookupError)
    def not_found(error):
        """The user or incident does not exist (LookupError)."""
        return back_with_error(error)

    @app.errorhandler(ValueError)
    def bad_request(error):
        """The data sent is not valid (ValueError)."""
        return back_with_error(error)
