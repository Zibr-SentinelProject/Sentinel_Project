"""Pruebas unitarias de AttachmentService.

Los archivos se escriben en un directorio temporal para no ensuciar el proyecto.
"""
import os
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models.attachement import Attachment
from app.models.user import Employee
from app.services.attachment_service import AttachmentService


@pytest.fixture(autouse=True)
def in_tmp_dir(tmp_path, monkeypatch):
    # Attachment.PATHFILE es relativo al directorio de trabajo.
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def attachment_repo():
    repo = MagicMock()
    repo.create.side_effect = lambda attachment: attachment
    return repo


@pytest.fixture
def incident_service():
    service = MagicMock()
    service.find_incident.side_effect = lambda incident_id: SimpleNamespace(id=incident_id)
    service.get_incident.side_effect = lambda user, incident_id: SimpleNamespace(id=incident_id)
    service.can_participate.return_value = True
    return service


@pytest.fixture
def service(attachment_repo, incident_service):
    return AttachmentService(attachment_repo, incident_service)


@pytest.fixture
def user():
    return Employee("Ana", "ana@example.com", "secret")


def stored_files():
    """Archivos que hay ahora mismo en el directorio de adjuntos."""
    if not os.path.isdir(Attachment.PATHFILE):
        return []
    return os.listdir(Attachment.PATHFILE)


def test_add_attachment_writes_file_and_registers_it(service, attachment_repo, user):
    incident = uuid.uuid4()

    created = service.add_attachment(user, incident, "foto.png", "image/png", b"datos")

    assert created.incident_id == incident
    assert created.filename == "foto.png"
    with open(created.path, "rb") as file:
        assert file.read() == b"datos"
    attachment_repo.create.assert_called_once_with(created)


def test_add_attachment_stores_file_under_unique_name(service, user):
    first = service.add_attachment(user, uuid.uuid4(), "foto.png", "image/png", b"uno")
    second = service.add_attachment(user, uuid.uuid4(), "foto.png", "image/png", b"dos")

    assert first.path != second.path
    with open(first.path, "rb") as file:
        assert file.read() == b"uno"
    with open(second.path, "rb") as file:
        assert file.read() == b"dos"
    assert first.filename == second.filename == "foto.png"


def test_add_attachment_strips_directories_from_filename(service, user):
    created = service.add_attachment(user, uuid.uuid4(), "../../secreto.png", "image/png", b"x")

    assert created.filename == "secreto.png"
    assert os.path.dirname(created.path) == Attachment.PATHFILE.rstrip("/")
    assert stored_files() == [os.path.basename(created.path)]


def test_add_attachment_rejects_empty_filename(service, attachment_repo, user):
    with pytest.raises(ValueError):
        service.add_attachment(user, uuid.uuid4(), "", "image/png", b"x")

    attachment_repo.create.assert_not_called()


def test_add_attachment_denies_user_not_participating(service, incident_service, attachment_repo, user):
    incident_service.can_participate.return_value = False

    with pytest.raises(PermissionError):
        service.add_attachment(user, uuid.uuid4(), "foto.png", "image/png", b"x")

    attachment_repo.create.assert_not_called()
    assert stored_files() == []


def test_add_attachment_rejects_disallowed_type_without_writing(service, attachment_repo, user):
    with pytest.raises(ValueError, match="File type not allowed"):
        service.add_attachment(user, uuid.uuid4(), "malo.zip", "application/zip", b"x")

    attachment_repo.create.assert_not_called()
    assert stored_files() == []


def test_add_attachment_rejects_file_too_big(service, attachment_repo, user):
    too_big = b"x" * (Attachment.MAX_FILE_SIZE_MB * 1024 * 1024 + 1)

    with pytest.raises(ValueError, match="File is too big"):
        service.add_attachment(user, uuid.uuid4(), "grande.pdf", "application/pdf", too_big)

    attachment_repo.create.assert_not_called()


def test_add_attachment_removes_file_when_db_insert_fails(service, attachment_repo, user):
    attachment_repo.create.side_effect = RuntimeError("db caída")

    with pytest.raises(RuntimeError):
        service.add_attachment(user, uuid.uuid4(), "foto.png", "image/png", b"x")

    assert stored_files() == []


def test_list_attachments_returns_repo_results(service, attachment_repo, user):
    incident = uuid.uuid4()
    attachments = [Attachment(incident, "a.png", "image/png", 1)]
    attachment_repo.get_all_by_incident.return_value = attachments

    assert service.list_attachments(user, incident) == attachments
    attachment_repo.get_all_by_incident.assert_called_once_with(incident)


def test_get_attachment_checks_incident_visibility(service, attachment_repo, incident_service, user):
    attachment = Attachment(uuid.uuid4(), "a.png", "image/png", 1)
    attachment_repo.get_by_id.return_value = attachment

    assert service.get_attachment(user, attachment.id) is attachment
    incident_service.get_incident.assert_called_once_with(user, attachment.incident_id)


def test_get_attachment_raises_when_missing(service, attachment_repo, user):
    attachment_repo.get_by_id.return_value = None

    with pytest.raises(LookupError):
        service.get_attachment(user, uuid.uuid4())


def test_get_attachment_propagates_permission_error(service, attachment_repo, incident_service, user):
    attachment_repo.get_by_id.return_value = Attachment(uuid.uuid4(), "a.png", "image/png", 1)
    incident_service.get_incident.side_effect = PermissionError("no puedes ver el ticket")

    with pytest.raises(PermissionError):
        service.get_attachment(user, uuid.uuid4())


def test_delete_attachment_removes_row_and_file(service, attachment_repo, user):
    attachment = service.add_attachment(user, uuid.uuid4(), "borrar.png", "image/png", b"x")
    attachment_repo.get_by_id.return_value = attachment
    attachment_repo.delete.return_value = True

    assert service.delete_attachment(user, attachment.id) is True

    attachment_repo.delete.assert_called_once_with(attachment.id)
    assert not os.path.exists(attachment.path)


def test_delete_attachment_does_not_touch_other_attachments_with_same_name(service, attachment_repo, user):
    keep = service.add_attachment(user, uuid.uuid4(), "foto.png", "image/png", b"del otro ticket")
    doomed = service.add_attachment(user, uuid.uuid4(), "foto.png", "image/png", b"de este ticket")
    attachment_repo.get_by_id.return_value = doomed
    attachment_repo.delete.return_value = True

    service.delete_attachment(user, doomed.id)

    with open(keep.path, "rb") as file:
        assert file.read() == b"del otro ticket"


def test_delete_attachment_tolerates_missing_file(service, attachment_repo, user):
    attachment = Attachment(uuid.uuid4(), "fantasma.png", "image/png", 1)
    attachment_repo.get_by_id.return_value = attachment
    attachment_repo.delete.return_value = True

    assert service.delete_attachment(user, attachment.id) is True


def test_delete_attachment_denies_user_not_participating(service, attachment_repo, incident_service, user):
    attachment = service.add_attachment(user, uuid.uuid4(), "protegido.png", "image/png", b"x")
    attachment_repo.get_by_id.return_value = attachment
    incident_service.can_participate.return_value = False

    with pytest.raises(PermissionError):
        service.delete_attachment(user, attachment.id)

    attachment_repo.delete.assert_not_called()
    assert os.path.exists(attachment.path)


def test_delete_attachment_keeps_file_when_row_not_deleted(service, attachment_repo, user):
    attachment = service.add_attachment(user, uuid.uuid4(), "quedate.png", "image/png", b"x")
    attachment_repo.get_by_id.return_value = attachment
    attachment_repo.delete.return_value = False

    assert service.delete_attachment(user, attachment.id) is False
    assert os.path.exists(attachment.path)


def test_delete_attachment_raises_when_missing(service, attachment_repo, user):
    attachment_repo.get_by_id.return_value = None

    with pytest.raises(LookupError):
        service.delete_attachment(user, uuid.uuid4())
