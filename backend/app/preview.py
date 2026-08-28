from __future__ import annotations

import base64
import hashlib
import io
import mimetypes
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .core.config import settings
from .storage import db

PREVIEW_TTL_MINUTES = 60
MAX_PREVIEW_FILE_BYTES = 10 * 1024 * 1024


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _safe_root(root: Path) -> Path:
    resolved = root.resolve()
    data_root = settings.data_dir.resolve()
    if resolved != data_root and data_root not in resolved.parents:
        raise PermissionError("Preview root outside Assane data directory")
    if not resolved.is_dir():
        raise ValueError("Preview root not found")
    return resolved


def _entry_for(root: Path) -> str:
    for candidate in ("index.html", "dist/index.html", "build/index.html", "out/index.html"):
        if (root / candidate).is_file():
            return candidate
    raise ValueError("No preview entrypoint found")


def qr_data_url(url: str) -> str | None:
    try:
        import qrcode
        image = qrcode.make(url)
        output = io.BytesIO()
        image.save(output, format="PNG")
        encoded = base64.b64encode(output.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except (ImportError, OSError, ValueError):
        return None


def create_preview(user_id: str, task_id: str, root: Path, ttl_minutes: int = PREVIEW_TTL_MINUTES) -> dict[str, Any]:
    safe_root = _safe_root(root)
    total_bytes = sum(path.stat().st_size for path in safe_root.rglob("*") if path.is_file() and not path.is_symlink())
    if total_bytes > settings.max_preview_bytes:
        raise ValueError("Le workspace dépasse le quota de preview publique")
    entry = _entry_for(safe_root)
    token = secrets.token_urlsafe(32)
    link_id = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(minutes=max(5, min(ttl_minutes, 24 * 60)))
    db.create_preview_link(link_id, _hash_token(token), user_id, task_id, str(safe_root), entry, expires.isoformat())
    public_url = f"{settings.public_base_url.rstrip('/')}/preview/{token}/"
    return {
        "id": link_id,
        "token": token,
        "task_id": task_id,
        "entry_path": entry,
        "expires_at": expires.isoformat(),
        "status": "active",
        "url": public_url,
        "qr_data_url": qr_data_url(public_url),
    }


def resolve_preview(token: str, requested_path: str) -> tuple[Path, str] | None:
    if not token or len(token) > 200:
        return None
    link = db.get_preview_link_by_token(_hash_token(token))
    if not link or link["status"] != "active":
        return None
    try:
        if datetime.fromisoformat(link["expires_at"]) <= datetime.now(timezone.utc):
            return None
    except ValueError:
        return None
    root = Path(link["root_path"]).resolve()
    entry_path = str(link["entry_path"])
    entry_parent = Path(entry_path).parent
    requested = requested_path.strip("/")
    candidate_path = entry_path if not requested else str(entry_parent / requested) if str(entry_parent) != "." else requested
    candidate = (root / candidate_path).resolve()
    if candidate != root and root not in candidate.parents:
        return None
    if not candidate.is_file() or candidate.stat().st_size > MAX_PREVIEW_FILE_BYTES:
        return None
    mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
    return candidate, mime


def revoke_preview(user_id: str, preview_id: str) -> bool:
    return db.revoke_preview_link(preview_id, user_id)
