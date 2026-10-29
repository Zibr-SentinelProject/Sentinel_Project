from flask import Flask, jsonify, render_template

from app.db.database import check_connection, init_app as init_db


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    init_db(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        connected, detail = check_connection()
        body = {"status": "ok" if connected else "error", "database": detail}
        return jsonify(body), 200 if connected else 503

    return app
