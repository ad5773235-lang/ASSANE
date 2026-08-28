from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path

from ..core.config import settings
from . import db


def save_artifact(user_id: str, task_id: str, filename: str, content: bytes, mime_type: str) -> dict:
    if db.user_storage_bytes(user_id) + len(content) > settings.max_user_storage_bytes:
        raise ValueError("Le quota de stockage de ce compte est atteint")
    artifact_id = str(uuid.uuid4())
    safe_name = Path(filename).name or "artifact.bin"
    target = settings.data_dir / "artifacts" / user_id / artifact_id / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO artifacts(id, task_id, user_id, filename, path, mime_type, sha256, size_bytes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (artifact_id, task_id, user_id, safe_name, str(target), mime_type or "application/octet-stream", digest, len(content)),
        )
    return {
        "id": artifact_id,
        "task_id": task_id,
        "filename": safe_name,
        "mime_type": mime_type or "application/octet-stream",
        "size_bytes": len(content),
        "sha256": digest,
    }


def get_artifact(user_id: str, artifact_id: str) -> dict | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM artifacts WHERE id = ? AND user_id = ?",
            (artifact_id, user_id),
        ).fetchone()
    return dict(row) if row else None
