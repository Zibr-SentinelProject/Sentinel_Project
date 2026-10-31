from uuid import UUID

from flask import Blueprint, redirect, render_template, request

from app.db.database import get_db
from app.repositories.incident_repo import IncidentRepository
from app.repositories.user_repo import UserRepository
from app.routes.common import current_user, get_attachment_service, get_comment_service
from app.services.incident_service import IncidentService
from app.services.user_service import UserService

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
    source_url = request.form.get("source_url")
    service = IncidentService(IncidentRepository(get_db()))
    incident = service.create_incident(user, title, description, severity, source_url)

    # El adjunto es opcional y solo se puede añadir aqui
    file = request.files.get("file")
    if file is not None and file.filename:
        get_attachment_service().add_attachment(user, incident.id, file.filename, file.mimetype, file.read())
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
    # Solo los analistas asignan tickets, así que solo ellos necesitan la lista de analistas.
    analysts = UserService(UserRepository(get_db())).list_analysts() if user.is_analyst() else []
    # Solo participan (comentar, adjuntar) el creador y el analista asignado; la regla vive en el servicio.
    can_participate = service.can_participate(user, incident)
    return render_template("incident.html", user=user, incident=incident, comments=comments,
                           attachments=attachments, analysts=analysts, can_participate=can_participate)


@incidents_bp.post("/incidents/<uuid:incident_id>/assign")
def assign_incident(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    analyst_id = UUID(request.form.get("analyst_id"))
    service = IncidentService(IncidentRepository(get_db()))
    service.assign_incident(user, incident_id, analyst_id)
    return redirect(f"/incidents/{incident_id}")


@incidents_bp.post("/incidents/<uuid:incident_id>/close")
def close_incident(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    service = IncidentService(IncidentRepository(get_db()))
    service.close_incident(user, incident_id)
    return redirect(f"/incidents/{incident_id}")
