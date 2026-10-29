from html import escape

from flask import Flask, jsonify

from app.db.database import check_connection, init_app as init_db


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    init_db(app)

    @app.route("/")
    def index():
        connected, detail = check_connection()
        if connected:
            status = f"Conectado a la base de datos ({escape(detail)})"
        else:
            status = f"No conectado a la base de datos: {escape(detail)}"
        return (
            "<!doctype html>"
            "<html lang='es'><head><meta charset='utf-8'><title>Sentinel</title></head>"
            "<body>"
            "<h1>Sentinel Project</h1>"
            f"<p>{status}</p>"
            "</body></html>"
        )

    @app.route("/health")
    def health():
        connected, detail = check_connection()
        body = {"status": "ok" if connected else "error", "database": detail}
        return jsonify(body), 200 if connected else 503

    return app
