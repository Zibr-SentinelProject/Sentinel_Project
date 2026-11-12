from flask import Blueprint, redirect, render_template, request, session

from app.routes.common import current_user
from app.services.factory import get_user_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    """Shows the login form."""
    return render_template("login.html")


@auth_bp.post("/login")
def login():
    """Logs the user in with the email and password of the form.

    Returns:
        A redirect to the incidents if it works, or the login page with an error
        (400 if something is missing, 401 if the data is wrong).
    """
    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        return render_template("login.html", error="Email and password are required"), 400

    service = get_user_service()
    user = service.authenticate(email, password)
    if user is None:
        return render_template("login.html", error="Invalid email or password"), 401

    session.clear()
    session["user_id"] = str(user.id)
    # The name is stored so the header can show it without querying the DB on every page.
    session["user_name"] = user.name
    return redirect("/incidents")


@auth_bp.get("/register")
def register_page():
    """Shows the form to create an account."""
    return render_template("register.html")


@auth_bp.post("/register")
def register():
    """Creates an employee account with the data of the form and logs it in.

    Returns:
        A redirect to the incidents if it works, or the register page with an error (400).
    """
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    if not name or not email or not password:
        return render_template("register.html", error="Name, email and password are required"), 400

    service = get_user_service()
    try:
        user = service.register(name, email, password)
    except ValueError as error:
        return render_template("register.html", error=str(error)), 400

    # The new employee is logged in right away, the same way as in login.
    session.clear()
    session["user_id"] = str(user.id)
    session["user_name"] = user.name
    return redirect("/incidents")


@auth_bp.get("/password")
def password_page():
    """Shows the form to change the password. If the user is not logged in, it goes to the login."""
    user = current_user()
    if user is None:
        return redirect("/login")
    return render_template("edit_user.html", user=user)


@auth_bp.post("/password")
def change_password():
    """Changes the password of the logged user. If the user is not logged in, it goes to the login.

    Returns:
        The same form with a success message, or with an error (400) if the current password is wrong
        or the new one is empty.
    """
    user = current_user()
    if user is None:
        return redirect("/login")

    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    try:
        get_user_service().change_password(user, current_password, new_password)
    except ValueError as error:
        # Shown in the same form, like the login error.
        return render_template("edit_user.html", user=user, error=str(error)), 400
    return render_template("edit_user.html", user=user, success="Contraseña actualizada")


@auth_bp.post("/logout")
def logout():
    """Logs the user out and goes to the login.

    It is a POST so another site cannot log the user out with a simple link or image."""
    session.clear()
    return redirect("/login")
