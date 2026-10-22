import os

import pymysql
from dotenv import load_dotenv
from flask import g

load_dotenv()


def create_connection():
    """Open a new PyMySQL connection using the settings in the .env file."""
    return pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    charset="utf8mb4",
    autocommit=False, 
    )


def get_db():
    """Return the connection for the current request, creating it if needed.

    Pass the result to the repositories, e.g. CommentRepository(get_db()).
    """
    if "db" not in g:
        g.db = create_connection()
    return g.db


def close_db(error=None):
    """Close the request's connection (registered as a teardown handler)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """Hook the database into the Flask app. Call from the app factory."""
    app.teardown_appcontext(close_db)