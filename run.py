"""Entry point of Sentinel.

It creates the Flask app. Docker starts it with `flask --app run run`, which looks for the
`app` variable in this file. It can also be started with `python run.py`.
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Only when the file is run directly (python run.py), not when Flask imports it.
    # Debug mode is on unless FLASK_ENV is set to "production".
    debug = os.getenv("FLASK_ENV", "development") != "production"
    app.run(debug=debug)
