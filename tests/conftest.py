import pytest


@pytest.fixture(autouse=True)
def in_tmp_dir(tmp_path, monkeypatch):
    """Attachments are saved in a path relative to the working directory: every test gets a temporary one."""
    monkeypatch.chdir(tmp_path)
