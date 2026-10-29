from uuid import UUID

from app.models.user import User


class IncidentService:

    def __init__(self, incident_repo):
        self.incident_repo = incident_repo

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
