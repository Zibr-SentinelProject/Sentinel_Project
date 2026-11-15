from uuid import UUID

from app.models.attachment import Attachment
from app.models.incident import Incident
from app.models.user import User
from app.services.authorization import (
    ASSIGN_INCIDENT,
    BE_ASSIGNEE,
    CLOSE_INCIDENT,
    LIST_ALL_INCIDENTS,
    LIST_INCIDENTS,
    VIEW_INCIDENT,
    authorize,
    require,
)
from app.services.link_service import fetch_page_title


class IncidentService:
    """Rules for the incidents: who can create, see, assign and close them."""

    def __init__(self, incident_repo, user_service):
        """Creates the service.

        Args:
            incident_repo (IncidentRepository): Used to save and read the incidents
            user_service (UserService): Used to load the user an incident is assigned to
        """
        self.incident_repo = incident_repo
        self.user_service = user_service

    def create_incident(self, user: User, title: str, description: str, severity: int, source_url: str = None,
                        filename: str = None, filetype: str = None, content: bytes = None):
        """Any logged-in user can create it; it is registered under their name as the creator.
        If it has a source link, the server visits it to store the page title.
        If it comes with a file, it is saved together with the ticket (the only moment a file can be attached)."""
        incident = Incident(user.id, title, description, severity)
        if source_url:
            incident.source_url = source_url
            incident.source_title = fetch_page_title(source_url)
        if filename:
            incident.attachment = Attachment(incident.id, filename, filetype, len(content))
            incident.attachment.save_file(content)

        try:
            return self.incident_repo.create(incident)
        except Exception:
            # If the ticket could not be saved, we don't leave the file orphaned.
            if incident.attachment:
                incident.attachment.remove_file()
            raise

    def list_incidents(self, user: User, title: str = None, severity: int = None, state: int = None):
        """Who can see every ticket gets all of them; the rest only the ones they created.
        Filters by title, severity and state.

        The scope is chosen in the query, so the tickets of other people are never loaded.
        """
        require(user, LIST_INCIDENTS)
        if authorize(user, LIST_ALL_INCIDENTS):
            incidents = self.incident_repo.get_all()
        else:
            incidents = self.incident_repo.get_by_user(user.id)
        if title:
            incidents = [incident for incident in incidents if title.lower() in incident.title.lower()]
        if severity is not None:
            incidents = [incident for incident in incidents if incident.severity == severity]
        if state is not None:
            incidents = [incident for incident in incidents if incident.state == state]
        return incidents

    def get_incident(self, user: User, incident_id: UUID, action: str = VIEW_INCIDENT):
        """The only way to load an incident for a user: it loads it and checks that the user can do the action.

        A missing incident and an incident the user may not use give the same answer (404), so nobody
        can find out which incidents exist.

        Args:
            user (User): The user who asks
            incident_id (UUID): The UUID of the incident
            action (str): What the user wants to do with it (a constant of app.services.authorization)

        Raises:
            LookupError: If the incident does not exist
            AccessDeniedError: If the user cannot do the action with this incident

        Returns:
            incident (Incident): The incident found
        """
        incident = self.incident_repo.get_by_id(incident_id)
        if incident is None:
            raise LookupError("Incident not found")
        require(user, action, incident)
        return incident

    def assign_incident(self, user: User, incident_id: UUID, analyst_id: UUID):
        """With no analyst, any analyst can claim it or assign it to another.
        If it already has an analyst, only that analyst can change it.

        authorize(ASSIGN_INCIDENT) only says who may assign; who RECEIVES it is checked here,
        with BE_ASSIGNEE, because analyst_id comes from the browser and cannot be trusted.

        Raises:
            AccessDeniedError: If the user cannot assign this incident
            LookupError: If the incident or the analyst do not exist
            ValueError: If the analyst cannot be assigned incidents
        """
        incident = self.get_incident(user, incident_id, ASSIGN_INCIDENT)
        assignee = self.user_service.get_user(analyst_id)
        if not authorize(assignee, BE_ASSIGNEE):
            raise ValueError("This user cannot be assigned incidents")
        incident.assign(analyst_id)
        return self.incident_repo.update(incident.id, incident)

    def close_incident(self, user: User, incident_id: UUID):
        """Only the assigned analyst can close the ticket."""
        incident = self.get_incident(user, incident_id, CLOSE_INCIDENT)
        incident.close()
        return self.incident_repo.update(incident.id, incident)
