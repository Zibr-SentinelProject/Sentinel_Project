import os

from flask import Flask

from app.db.database import init_app as init_db
from app.routes.attachments import attachments_bp
from app.routes.auth import auth_bp
from app.routes.comments import comments_bp
from app.routes.common import main_bp, register_error_handlers
from app.routes.incidents import incidents_bp
from app.routes.users import users_bp


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    # The login session is signed with this key; without it Flask cannot store the session.
    app.secret_key = os.getenv("SECRET_KEY")
    init_db(app)
    register_error_handlers(app)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(users_bp)

    return app
