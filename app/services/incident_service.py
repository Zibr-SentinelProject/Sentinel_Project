from uuid import UUID

from app.models.incident import Incident
from app.models.user import User


class IncidentService:

    def __init__(self, incident_repo):
        self.incident_repo = incident_repo

    def create_incident(self, user: User, title: str, description: str, severity: int):
        """Lo crea cualquier usuario logueado; queda a su nombre como creador."""
        incident = Incident(user.id, title, description, severity)
        return self.incident_repo.create(incident)

    def list_incidents(self, user: User, title: str = None, severity: int = None, state: int = None):
        """El analista ve todos los tickets; el empleado solo los suyos. Filtra por título, severidad y estado."""
        incidents = self.incident_repo.get_all()
        if not user.view_all_incidents():
            incidents = [incident for incident in incidents if incident.user_id == user.id]
        if title:
            incidents = [incident for incident in incidents if title.lower() in incident.title.lower()]
        if severity is not None:
            incidents = [incident for incident in incidents if incident.severity == severity]
        if state is not None:
            incidents = [incident for incident in incidents if incident.state == state]
        return incidents

    def find_incident(self, incident_id: UUID):
        incident = self.incident_repo.get_by_id(incident_id)
        if incident is None:
            raise LookupError("Incident not found")
        return incident

    def get_incident(self, user: User, incident_id: UUID):
        """Lo ve el analista, o el empleado que creó el ticket."""
        incident = self.find_incident(incident_id)
        if not user.view_all_incidents() and incident.user_id != user.id:
            raise PermissionError("You cannot view this incident")
        return incident

    def can_participate(self, user: User, incident) -> bool:
        """Participan el creador del ticket y el analista asignado."""
        return incident.user_id == user.id or incident.analyst_id == user.id

    def assign_incident(self, user: User, incident_id: UUID, analyst_id: UUID):
        """Sin analista, cualquier analista puede reclamarlo o asignarlo a otro.
        Si ya tiene analista, solo ese analista puede cambiarlo."""
        if not user.is_analyst():
            raise PermissionError("Only analysts can assign incidents")
        incident = self.find_incident(incident_id)
        if incident.analyst_id is not None and incident.analyst_id != user.id:
            raise PermissionError("Only the assigned analyst can reassign this incident")
        incident.assign(analyst_id)
        return self.incident_repo.update(incident.id, incident)

    def close_incident(self, user: User, incident_id: UUID):
        """Solo el analista asignado puede cerrar el ticket."""
        incident = self.find_incident(incident_id)
        if incident.analyst_id != user.id:
            raise PermissionError("Only the assigned analyst can close this incident")
        incident.close()
        return self.incident_repo.update(incident.id, incident)
