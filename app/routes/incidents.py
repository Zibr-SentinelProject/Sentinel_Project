from flask import Blueprint, redirect, render_template, request

from app.db.database import get_db
from app.repositories.incident_repo import IncidentRepository
from app.routes.common import current_user, get_attachment_service, get_comment_service
from app.services.incident_service import IncidentService

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.get("/incidents")
def list_incidents():
    user = current_user()
    if user is None:
        return redirect("/login")

    title = request.args.get("title")
    severity = request.args.get("severity", "")
    state = request.args.get("state", "")
    service = IncidentService(IncidentRepository(get_db()))

    incidents = service.list_incidents(
        user,
        title=title,
        severity=int(severity) if severity else None,
        state=int(state) if state else None,
    )
    return render_template("incidents.html", user=user, incidents=incidents, title=title,
                           severity=severity, state=state)


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
    service = IncidentService(IncidentRepository(get_db()))
    service.create_incident(user, title, description, severity)
    return redirect("/incidents")


@incidents_bp.get("/incidents/<uuid:incident_id>")
def incident_detail(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    service = IncidentService(IncidentRepository(get_db()))
    incident = service.get_incident(user, incident_id)
    comments = get_comment_service().list_comments(user, incident_id)
    attachments = get_attachment_service().list_attachments(user, incident_id)
    return render_template("incident.html", user=user, incident=incident, comments=comments,
                           attachments=attachments)
