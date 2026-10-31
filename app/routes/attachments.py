import os

from flask import Blueprint, redirect, send_file

from app.routes.common import current_user, get_attachment_service

attachments_bp = Blueprint("attachments", __name__)


@attachments_bp.get("/attachments/<uuid:attachment_id>")
def download_attachment(attachment_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    attachment = get_attachment_service().get_attachment(user, attachment_id)
    # send_file resolves relative paths from the app folder, not from where it was launched; hence abspath.
    return send_file(os.path.abspath(attachment.path), download_name=attachment.filename)
