from flask import Blueprint, redirect, send_file

from app.routes.common import current_user
from app.services.authorization import DOWNLOAD_ATTACHMENT
from app.services.factory import get_incident_service

attachments_bp = Blueprint("attachments", __name__)


@attachments_bp.get("/incidents/<uuid:incident_id>/attachment")
def download_attachment(incident_id):
    """Downloads the file attached to an incident. If the user is not logged in, it goes to the login.

    Args:
        incident_id (UUID): The incident, taken from the url

    Raises:
        LookupError: If the incident has no attachment

    Returns:
        file: The file, with its original name
    """
    user = current_user()
    if user is None:
        return redirect("/login")

    # get_incident checks that the user can download the file of this ticket; the attachment comes with it.
    attachment = get_incident_service().get_incident(user, incident_id, DOWNLOAD_ATTACHMENT).attachment
    if attachment is None:
        raise LookupError("This incident has no attachment")
    # send_file resolves relative paths from the app folder, not from where it was launched; hence resolve().
    return send_file(
    attachment.path.resolve(),
    as_attachment=True,
    download_name=attachment.filename,
)
