from flask import Blueprint, redirect, request

from app.routes.common import current_user, get_comment_service

comments_bp = Blueprint("comments", __name__)


@comments_bp.post("/incidents/<uuid:incident_id>/comments")
def add_comment(incident_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    content = request.form.get("content")
    get_comment_service().add_comment(user, incident_id, content)
    return redirect(f"/incidents/{incident_id}")
