from uuid import UUID

from flask import Blueprint, make_response, redirect, render_template, request

from app.routes.common import current_user
from app.services.factory import (
    get_attachment_service,
    get_comment_service,
    get_incident_service,
    get_user_service,
)

# How long the browser remembers the default severity filter (in seconds).
COOKIE_ONE_YEAR = 365 * 24 * 3600

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.get("/incidents")
def list_incidents():
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
                                             severity=severity, state=state))
    # The severity chosen in the filter becomes the default for the next visits.
    if "severity" in request.args:
        if severity:
            response.set_cookie("default_severity", severity, max_age=COOKIE_ONE_YEAR)
        else:
            response.delete_cookie("default_severity")
    return response


@incidents_bp.get("/incidents/new")
def new_incident_page():
    user = current_user()
    if user is None:
        return redirect("/login")
    return render_template("new_incident.html", user=user)


@incidents_bp.post("/incidents/new")
def create_incident():
    user = current_user()
    if user is None:
        return redirect("/login")

    title = request.form.get("title")
    description = request.form.get("description")
    severity = int(request.form.get("severity"))
    source_url = request.form.get("source_url")
    service = get_incident_service()
    incident = service.create_incident(user, title, description, severity, source_url)

    # The attachment is optional and can only be added here
    file = request.files.get("file")
    if file is not None and file.filename:
        get_attachment_service().add_attachment(user, incident.id, file.filename, file.mimetype, file.read())
    return redirect("/incidents")


@incidents_bp.get("/incidents/<uuid:incident_id>")
def incident_detail(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    service = get_incident_service()
    incident = service.get_incident(user, incident_id)
    comments = get_comment_service().list_comments(user, incident_id)
    attachments = get_attachment_service().list_attachments(user, incident_id)
    # Only analysts assign tickets, so only they need the list of analysts.
    analysts = get_user_service().list_analysts() if user.is_analyst() else []
    # Only the creator and the assigned analyst participate (comment, attach); the rule lives in the service.
    can_participate = service.can_participate(user, incident)
    return render_template("incident.html", user=user, incident=incident, comments=comments,
                           attachments=attachments, analysts=analysts, can_participate=can_participate)


@incidents_bp.post("/incidents/<uuid:incident_id>/assign")
def assign_incident(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    analyst_id = UUID(request.form.get("analyst_id"))
    service = get_incident_service()
    service.assign_incident(user, incident_id, analyst_id)
    return redirect(f"/incidents/{incident_id}")


@incidents_bp.post("/incidents/<uuid:incident_id>/close")
def close_incident(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    service = get_incident_service()
    service.close_incident(user, incident_id)
    return redirect(f"/incidents/{incident_id}")
