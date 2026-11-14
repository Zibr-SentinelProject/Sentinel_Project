

VIEW_INCIDENT = "view_incident"
LIST_INCIDENTS = "list_incidents"
LIST_ALL_INCIDENTS = "list_all_incidents"
BE_ASSIGNEE = "be_assignee"
DOWNLOAD_ATTACHMENT = "download_attachment"
COMMENT_INCIDENT = "comment_incident"
ASSIGN_INCIDENT = "assign_incident"
CLOSE_INCIDENT = "close_incident"
MANAGE_USERS = "manage_users"


def authorize(user, action: str, incident=None) -> bool:

    if user is None:
        return False

    # Actions that are not about one incident.
    if action == MANAGE_USERS:
        return bool(user.admin_all_users())
    if action == LIST_INCIDENTS:
        # Any user can ask for the list; LIST_ALL_INCIDENTS decides what is inside it.
        return True
    if action == LIST_ALL_INCIDENTS:
        return bool(user.view_all_incidents())
    if action == BE_ASSIGNEE:
        # Whether `user` can receive an assignment. ASSIGN_INCIDENT only checks who assigns, not who receives.
        return bool(user.handle_incidents())

    # Every other action is about one incident: without it, deny.
    if incident is None:
        return False

    is_creator = bool(incident.user_id == user.id)
    # Being the assigned analyst only counts while the user still handles incidents (e.g. not demoted).
    is_assigned = bool(user.handle_incidents() and incident.analyst_id == user.id)

    if action in (VIEW_INCIDENT, DOWNLOAD_ATTACHMENT):
        return bool(user.view_all_incidents()) or is_creator
    if action == COMMENT_INCIDENT:
        return is_creator or is_assigned
    if action == ASSIGN_INCIDENT:
        # Free incident: any analyst can take it. Taken: only its analyst can pass it on.
        return bool(user.handle_incidents() and (incident.analyst_id is None or is_assigned))
    if action == CLOSE_INCIDENT:
        return is_assigned

    # Unknown action: deny. Keep this as the last line.
    return False


class AccessDeniedError(Exception):
    """A logged-in user is not allowed to do the action.

    It is not a PermissionError on purpose: the app answers it with its own error page (see
    register_error_handlers) and not with the flash + redirect used for PermissionError.
    Someone who is not logged in never gets here: the login check comes first.

    Attributes:
        status (int): The HTTP code to answer with (404 or 403, see require).
    """

    def __init__(self, status: int):
        super().__init__("Access denied")
        self.status = status


def require(user, action: str, incident=None):
    """Same as authorize(), but raises AccessDeniedError if the answer is no. Routes and services call this one.

    The code is always chosen here, so every denial looks the same:
    404 when the action is about an incident (we do not confirm that it exists),
    403 when there is no object, only the role of the user (e.g. MANAGE_USERS).

    Args:
        user (User): The logged-in user (see authorize for BE_ASSIGNEE).
        action (str): One of the action constants of this module.
        incident (Incident, optional): The incident the action is about, when it has one.

    Raises:
        AccessDeniedError: If authorize says no.
    """
    if not authorize(user, action, incident):
        raise AccessDeniedError(404 if incident is not None else 403)
