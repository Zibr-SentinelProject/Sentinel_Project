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
    """Creates and configures the Flask app (application factory).

    It sets the secret key, connects the database, registers the error handlers and adds
    the blueprints (groups of routes). Flask and the tests call it to get a new app.

    Returns:
        Flask: The app, ready to run
    """
    app = Flask(__name__)
    # The login session is signed with this key; without it Flask cannot store the session.
    app.secret_key = os.getenv("SECRET_KEY")
    # Opens one database connection per request and closes it when the request ends.
    init_db(app)
    # Turns the exceptions of the services (PermissionError, LookupError, ValueError) into messages.
    register_error_handlers(app)
    # Each blueprint groups the routes of one topic.
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(users_bp)

    return app
