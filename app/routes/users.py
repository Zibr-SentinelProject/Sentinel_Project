from flask import Blueprint, redirect, render_template, request

from app.models.user import ROLE_CLASSES
from app.routes.common import requires_permission
from app.services.authorization import MANAGE_USERS
from app.services.factory import get_user_service

users_bp = Blueprint("users", __name__)


@users_bp.get("/users/new")
@requires_permission(MANAGE_USERS)
def new_user_page(user):
    """Shows the form to create a user. Only whoever manages the users can see it.

    If the user is not logged in, it goes to the login; without permission it answers 403.
    """
    return render_template("new_user.html", user=user, roles=ROLE_CLASSES)


@users_bp.post("/users/new")
@requires_permission(MANAGE_USERS)
def create_user(user):
    """Creates a user, with the role chosen, from the form. Only whoever manages the users can do it.

    If the user is not logged in, it goes to the login; without permission it answers 403.
    The role is checked against ROLE_CLASSES in the service. When it works, it goes to the list of incidents.
    """
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")
    get_user_service().create_user(user, name, email, password, role)
    return redirect("/incidents")


@users_bp.get("/users")
@requires_permission(MANAGE_USERS)
def list_users(user):
    """Shows the list of users. Only whoever manages the users can see it.

    If the user is not logged in, it goes to the login; without permission it answers 403.
    """
    users = get_user_service().list_users(user)
    return render_template("users.html", user=user, users=users, roles=ROLE_CLASSES)


@users_bp.post("/users/<uuid:user_id>/role")
@requires_permission(MANAGE_USERS)
def change_role(user, user_id):
    """Changes the role of a user to the one chosen in the form. Only whoever manages the users can do it.

    If the user is not logged in, it goes to the login; without permission it answers 403.
    The role is checked against ROLE_CLASSES in the service. When it works, it goes back to the list of users.

    Args:
        user (User): The logged-in user, given by requires_permission
        user_id (UUID): The user to change, taken from the url
    """
    get_user_service().change_role(user, user_id, request.form.get("role"))
    return redirect("/users")
