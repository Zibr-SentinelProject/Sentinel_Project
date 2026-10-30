from flask import Blueprint, redirect, render_template, request

from app.db.database import get_db
from app.repositories.incident_repo import IncidentRepository
from app.routes.common import current_user
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
