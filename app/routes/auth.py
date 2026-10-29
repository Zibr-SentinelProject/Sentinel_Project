from flask import Blueprint, jsonify, redirect, render_template, request, session

from app.db.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.user_service import UserService

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    return render_template("login.html")


@auth_bp.post("/login")
def login():
    # El formulario de la web envía datos de formulario; la API envía JSON.
    from_form = not request.is_json
    data = request.form if from_form else (request.get_json(silent=True) or {})
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return _login_failed("Email and password are required", 400, from_form)

    service = UserService(UserRepository(get_db()))
    user = service.authenticate(email, password)
    if user is None:
        return _login_failed("Invalid email or password", 401, from_form)

    # Guardamos solo el id; el resto de datos se leen de la BD en cada petición.
    session.clear()
    session["user_id"] = str(user.id)
    if from_form:
        return redirect("/")
    return jsonify(id=str(user.id), name=user.name, email=user.email, role=user.ROLE), 200


def _login_failed(message, status, from_form):
    """Con formulario vuelve a mostrar la página con el error; con JSON devuelve el error."""
    if from_form:
        return render_template("login.html", error=message), status
    return jsonify(error=message), status
