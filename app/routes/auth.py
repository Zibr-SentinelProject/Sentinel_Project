from flask import Blueprint, jsonify, request, session

from app.db.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.user_service import UserService

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify(error="Email and password are required"), 400

    service = UserService(UserRepository(get_db()))
    user = service.authenticate(email, password)
    if user is None:
        return jsonify(error="Invalid email or password"), 401

    # Guardamos solo el id; el resto de datos se leen de la BD en cada petición.
    session.clear()
    session["user_id"] = str(user.id)
    return jsonify(id=str(user.id), name=user.name, email=user.email, role=user.ROLE), 200
