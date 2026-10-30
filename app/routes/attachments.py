import os

from flask import Blueprint, redirect, request, send_file

from app.routes.common import current_user, get_attachment_service

attachments_bp = Blueprint("attachments", __name__)


@attachments_bp.post("/incidents/<uuid:incident_id>/attachment")
def upload_attachment(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    # El adjunto es opcional: si no se eligió archivo, se vuelve al detalle sin hacer nada.
    file = request.files.get("file")
    if file is not None and file.filename:
        get_attachment_service().add_attachment(user, incident_id, file.filename, file.mimetype, file.read())
    return redirect(f"/incidents/{incident_id}")


@attachments_bp.get("/attachments/<uuid:attachment_id>")
def download_attachment(attachment_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    attachment = get_attachment_service().get_attachment(user, attachment_id)
    # send_file resuelve rutas relativas desde la carpeta de la app, no desde donde se lanzó; por eso abspath.
    return send_file(os.path.abspath(attachment.path), download_name=attachment.filename)
