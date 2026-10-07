from __future__ import annotations

import pytest

from app import logos
from app.main import app


@pytest.fixture(autouse=True)
def isolated_logo_directory(tmp_path, monkeypatch):
    """Keep generated seed, upload, and comparison images out of data/logos."""
    directory = tmp_path / "logos"
    monkeypatch.setattr(logos, "LOGO_DIRECTORY", directory)
    monkeypatch.setattr(logos, "UPLOAD_LOGO_DIRECTORY", directory / "uploads")

    # The application mounts StaticFiles during import, so point that mount at
    # this test's directory as well for upload-serving coverage.
    mount = next(route for route in app.routes if getattr(route, "name", None) == "logos")
    mount.app.directory = str(directory)
    mount.app.all_directories = [str(directory)]
    yield
