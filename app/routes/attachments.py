from flask import Blueprint, redirect, send_file

from app.routes.common import current_user
from app.services.factory import get_incident_service

attachments_bp = Blueprint("attachments", __name__)


@attachments_bp.get("/incidents/<uuid:incident_id>/attachment")
def download_attachment(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    # get_incident already checks that the user can view the ticket, and the attachment comes with it.
    attachment = get_incident_service().get_incident(user, incident_id).attachment
    if attachment is None:
        raise LookupError("This incident has no attachment")
    # send_file resolves relative paths from the app folder, not from where it was launched; hence resolve().
    return send_file(attachment.path.resolve(), download_name=attachment.filename)
