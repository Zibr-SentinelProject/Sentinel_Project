from uuid import UUID

from flask import Blueprint, make_response, redirect, render_template, request

from app.routes.common import current_user
from app.services.authorization import (
    ASSIGN_INCIDENT,
    CLOSE_INCIDENT,
    COMMENT_INCIDENT,
    MANAGE_USERS,
    authorize,
)
from app.services.factory import (
    get_comment_service,
    get_incident_service,
    get_user_service,
)

# How long the browser remembers the default severity filter (in seconds).
COOKIE_ONE_YEAR = 365 * 24 * 3600

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.get("/incidents")
def list_incidents():
    """Shows the list of incidents, filtered by title, severity and state from the url.

    Analysts see all of them and employees only their own. The severity chosen is saved in a cookie
    as the default filter. If the user is not logged in, it goes to the login.
    """
    user = current_user()
    if user is None:
        return redirect("/login")

    title = request.args.get("title")
    # Without a severity in the URL, the default filter saved in the cookie is applied.
    severity = request.args.get("severity", request.cookies.get("default_severity", ""))
    state = request.args.get("state", "")
    service = get_incident_service()

    incidents = service.list_incidents(
        user,
        title=title,
        severity=int(severity) if severity else None,
        state=int(state) if state else None,
    )
    response = make_response(render_template("incidents.html", user=user, incidents=incidents, title=title,
                                             severity=severity, state=state,
                                             can_manage_users=authorize(user, MANAGE_USERS)))
    # The severity chosen in the filter becomes the default for the next visits.
    if "severity" in request.args:
        if severity:
            response.set_cookie("default_severity", severity, max_age=COOKIE_ONE_YEAR)
        else:
            response.delete_cookie("default_severity")
    return response


@incidents_bp.get("/incidents/new")
def new_incident_page():
    """Shows the form to report an incident. If the user is not logged in, it goes to the login."""
    user = current_user()
    if user is None:
        return redirect("/login")
    return render_template("new_incident.html", user=user)


@incidents_bp.post("/incidents/new")
def create_incident():
    """Creates an incident with the data of the form (and the file, if there is one).

    If the user is not logged in, it goes to the login. When it works, it goes to the list of incidents.
    """
    user = current_user()
    if user is None:
        return redirect("/login")

    title = request.form.get("title")
    description = request.form.get("description")
    severity = int(request.form.get("severity"))
    source_url = request.form.get("source_url")
    service = get_incident_service()

    # The attachment is optional and can only be added here, together with the ticket.
    file = request.files.get("file")
    if file is not None and file.filename:
        service.create_incident(user, title, description, severity, source_url,
                                file.filename, file.mimetype, file.read())
    else:
        service.create_incident(user, title, description, severity, source_url)
    return redirect("/incidents")


@incidents_bp.get("/incidents/<uuid:incident_id>")
def incident_detail(incident_id):
    """Shows one incident with its comments.

    Analysts also get the list of analysts to assign it. If the user is not logged in, it goes to the login.

    Args:
        incident_id (UUID): The incident, taken from the url
    """
    user = current_user()
    if user is None:
        return redirect("/login")

    service = get_incident_service()
    incident = service.get_incident(user, incident_id)
    comments = get_comment_service().list_comments(user, incident_id)
    # The page only shows what the user can do, with the same rule the services apply when a form is sent.
    can_comment = authorize(user, COMMENT_INCIDENT, incident)
    can_assign = authorize(user, ASSIGN_INCIDENT, incident)
    can_close = authorize(user, CLOSE_INCIDENT, incident)
    # Only who can assign needs the list of users that can receive it.
    analysts = get_user_service().list_assignable_users() if can_assign else []
    return render_template("incident.html", user=user, incident=incident, comments=comments, analysts=analysts,
                           can_comment=can_comment, can_assign=can_assign, can_close=can_close)


@incidents_bp.post("/incidents/<uuid:incident_id>/assign")
def assign_incident(incident_id):
    """Assigns the incident to the analyst chosen in the form, then goes back to the incident.

    If the user is not logged in, it goes to the login.

    Args:
        incident_id (UUID): The incident, taken from the url
    """
    user = current_user()
    if user is None:
        return redirect("/login")

    # Without a default, a missing field is None and UUID(None) is a TypeError (a 500); "" is a ValueError.
    analyst_id = UUID(request.form.get("analyst_id", ""))
    service = get_incident_service()
    service.assign_incident(user, incident_id, analyst_id)
    return redirect(f"/incidents/{incident_id}")


@incidents_bp.post("/incidents/<uuid:incident_id>/close")
def close_incident(incident_id):
    """Closes the incident, then goes back to the incident. If the user is not logged in, it goes to the login.

    Args:
        incident_id (UUID): The incident, taken from the url
    """
    user = current_user()
    if user is None:
        return redirect("/login")

    service = get_incident_service()
    service.close_incident(user, incident_id)
    return redirect(f"/incidents/{incident_id}")
