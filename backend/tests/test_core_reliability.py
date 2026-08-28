from __future__ import annotations

from pathlib import Path

import pytest

from app.core import auth
from app.core.config import Settings, settings
from app.storage import db
from app.storage.artifacts import get_artifact, save_artifact


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


def test_artifacts_are_isolated_by_user(isolated_storage: Path) -> None:
    user_a = db.create_user("A", "Alpha", "a@example.test", "700000001", "hash")
    user_b = db.create_user("B", "Beta", "b@example.test", "700000002", "hash")
    artifact = save_artifact(user_a["id"], "general", "note.txt", b"private-a", "text/plain")

    assert get_artifact(user_a["id"], artifact["id"])["sha256"] == artifact["sha256"]
    assert get_artifact(user_b["id"], artifact["id"]) is None
    assert db.user_storage_bytes(user_a["id"]) == len(b"private-a")


def test_sessions_can_be_revoked(isolated_storage: Path) -> None:
    user = db.create_user("A", "Alpha", "session@example.test", "700000003", "hash")
    token = auth.create_session_token(user["id"])

    assert auth.read_session_token(token) == user["id"]
    assert auth.revoke_session_token(token) is True
    assert auth.read_session_token(token) is None


def test_production_configuration_rejects_unsafe_defaults() -> None:
    unsafe = Settings(env="production", jwt_secret="change-me", public_base_url="http://localhost:8000", cors_origins="*", runner_mode="local")
    with pytest.raises(RuntimeError):
        unsafe.validate_production()

    safe = Settings(env="production", jwt_secret="a" * 64, public_base_url="https://api.example.test", cors_origins="https://app.example.test", runner_mode="docker", sms_provider="http")
    safe.validate_production()


def test_queued_job_is_recovered_after_worker_interruption(isolated_storage: Path) -> None:
    user = db.create_user("A", "Alpha", "job@example.test", "700000004", "hash")
    task = db.create_task(user["id"], "test job")
    queued = db.enqueue_job("task", user["id"], task_id=task["id"])
    claimed = db.claim_next_job()
    assert claimed and claimed["id"] == queued["id"] and claimed["status"] == "running"

    assert db.recover_running_jobs() == 1
    recovered = db.claim_next_job()
    assert recovered and recovered["id"] == queued["id"] and recovered["attempts"] == 2
    db.finish_job(recovered["id"])
    assert db.get_job(recovered["id"], user["id"])["status"] == "succeeded"
