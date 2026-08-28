from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import settings
from app.storage import db


@pytest.fixture()
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    original_data_dir = settings.data_dir
    object.__setattr__(settings, "data_dir", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "assane.db")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "artifacts").mkdir()
    db.init_db()
    try:
        yield tmp_path
    finally:
        object.__setattr__(settings, "data_dir", original_data_dir)
