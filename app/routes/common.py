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
    """Protects a route that is not about one object (e.g. /users): login first, then the permission.

    It is a decorator with a parameter, so it is built in three layers:
        1. requires_permission(action) remembers WHICH permission is needed.
        2. decorator(view) receives the route function and returns the protected version of it.
        3. wrapper(...) is that protected version: it runs on EVERY request, before the route.
    Layers 1 and 2 run once, when the app starts. Only layer 3 runs on each visit.

    What the wrapper does on each request, in order:
        - Nobody logged in -> redirect to the login. The route does not run.
        - Logged in but without permission -> require raises AccessDeniedError, and the
          error handler answers with the error page. The route does not run.
        - Logged in and allowed -> the route runs and receives the user as its first
          argument, so it does not have to look the user up again.

    Usage (the route decorator goes first, the permission right under it):
        @bp.route("/users")
        @requires_permission(MANAGE_USERS)
        def list_users(user):
            ...

    Args:
        action (str): The permission to check, one of the constants of app.services.authorization.
    """
    def decorator(view):
        # wraps keeps the name of the original route; Flask needs a different name for each one.
        @wraps(view)
        def wrapper(*args, **kwargs):
            # 1. Who is logged in? (None if nobody)
            user = current_user()
            if user is None:
                return redirect("/login")
            # 2. Is this user allowed to do the action? Raises AccessDeniedError if not.
            require(user, action)
            # 3. Everything is fine: run the real route, giving it the user.
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
        """Something does not exist (LookupError): the same 404 page as a denied incident, never a redirect."""
        return render_template("error.html", status=404, message="Not found"), 404

    @app.errorhandler(ValueError)
    def bad_request(error):
        """The data sent is not valid (ValueError)."""
        return back_with_error(error)
