from flask import Blueprint, redirect, render_template, request

from app.db.database import get_db
from app.models.user import ROLE_CLASSES
from app.repositories.user_repo import UserRepository
from app.routes.common import current_user
from app.services.user_service import UserService

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
    UserService(UserRepository(get_db())).create_user(user, name, email, password, role)
    return redirect("/incidents")
