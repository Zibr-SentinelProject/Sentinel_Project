from flask import Blueprint, redirect, render_template, request, session

from app.db.database import get_db
from app.repositories.user_repo import UserRepository
from app.routes.common import current_user
from app.services.user_service import UserService

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    return render_template("login.html")


@auth_bp.post("/login")
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        return render_template("login.html", error="Email and password are required"), 400

    service = UserService(UserRepository(get_db()))
    user = service.authenticate(email, password)
    if user is None:
        return render_template("login.html", error="Invalid email or password"), 401

    session.clear()
    session["user_id"] = str(user.id)
    return redirect("/incidents")


@auth_bp.get("/password")
def password_page():
    user = current_user()
    if user is None:
        return redirect("/login")
    return render_template("password.html", user=user)


@auth_bp.post("/password")
def change_password():
    user = current_user()
    if user is None:
        return redirect("/login")

    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    try:
        UserService(UserRepository(get_db())).change_password(user, current_password, new_password)
    except ValueError as error:
        # Se muestra en el mismo formulario, como el error del login.
        return render_template("password.html", user=user, error=str(error)), 400
    return render_template("password.html", user=user, success="Contraseña actualizada")


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect("/login")
