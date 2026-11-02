"""Unit tests for the Attachment model: the file name saved in the DB and the full path built from it."""
import uuid
from pathlib import Path

from app.models.attachment import Attachment


def test_the_stored_name_is_the_id_plus_the_extension_of_the_original_file():
    attachment = Attachment(uuid.uuid4(), "informe.pdf", "application/pdf", 10)

    assert attachment.stored_name == f"{attachment.id}.pdf"


def test_the_full_path_is_built_from_the_folder_and_the_stored_name():
    attachment = Attachment(uuid.uuid4(), "foto.png", "image/png", 10)

    assert attachment.path == Attachment.folder() / attachment.stored_name


def test_changing_the_folder_changes_the_path_of_every_attachment(monkeypatch):
    attachment = Attachment(uuid.uuid4(), "foto.png", "image/png", 10, stored_name="abc.png")

    monkeypatch.setattr(Attachment, "PATHFILE", Path("otra_carpeta"))

    assert attachment.path == Path("otra_carpeta") / "abc.png"
