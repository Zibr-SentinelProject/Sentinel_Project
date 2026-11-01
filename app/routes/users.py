from flask import Blueprint, redirect, render_template, request

from app.models.user import ROLE_CLASSES
from app.routes.common import current_user
from app.services.factory import get_user_service

users_bp = Blueprint("users", __name__)


@users_bp.get("/users/new")
def new_user_page():
    user = current_user()
    if user is None:
        return redirect("/login")
    if not user.is_analyst():
        raise PermissionError("Only analysts can create users")
    return render_template("new_user.html", user=user, roles=ROLE_CLASSES)


@users_bp.post("/users/new")
def create_user():
    user = current_user()
    if user is None:
        return redirect("/login")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")
    get_user_service().create_user(user, name, email, password, role)
    return redirect("/incidents")


@users_bp.get("/users")
def list_users():
    user = current_user()
    if user is None:
        return redirect("/login")

    users = get_user_service().list_users(user)
    return render_template("users.html", user=user, users=users, roles=ROLE_CLASSES)


@users_bp.post("/users/<uuid:user_id>/role")
def change_role(user_id):
    user = current_user()
    if user is None:
        return redirect("/login")

    get_user_service().change_role(user, user_id, request.form.get("role"))
    return redirect("/users")
