from uuid import UUID

from flask import Blueprint, jsonify, render_template, session

from app.db.database import check_connection, get_db
from app.repositories.user_repo import UserRepository
from app.services.user_service import UserService

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/health")
def health():
    connected, detail = check_connection()
    body = {"status": "ok" if connected else "error", "database": detail}
    return jsonify(body), 200 if connected else 503


def current_user():
    """Devuelve el usuario de la sesión, o None si no hay sesión iniciada."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    try:
        return UserService(UserRepository(get_db())).get_user(UUID(user_id))
    except LookupError:
        # El usuario de la sesión ya no existe en la base de datos.
        session.clear()
        return None


def login_error():
    return jsonify(error="Login required"), 401


def register_error_handlers(app):
    """Los servicios lanzan excepciones; aquí las convertimos en respuestas HTTP para toda la app."""

    @app.errorhandler(PermissionError)
    def forbidden(error):
        return jsonify(error=str(error)), 403

    @app.errorhandler(LookupError)
    def not_found(error):
        return jsonify(error=str(error)), 404

    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify(error=str(error)), 400
