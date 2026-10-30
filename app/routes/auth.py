from flask import Blueprint, redirect, render_template, request, session

from app.db.database import get_db
from app.repositories.user_repo import UserRepository
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
