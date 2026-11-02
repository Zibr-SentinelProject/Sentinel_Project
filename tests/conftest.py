import pytest

from app.models.attachment import Attachment


@pytest.fixture(autouse=True)
def attachments_in_tmp_dir(tmp_path, monkeypatch):
    """Every test saves its attachments in a temporary folder, never in the real one."""
    monkeypatch.setattr(Attachment, "PATHFILE", tmp_path / "attachments")
