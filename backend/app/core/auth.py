from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone

from .config import settings
from ..storage import db


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"pbkdf2_sha256$210000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt64, digest64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt64.encode())
        expected = hash_password(password, salt).split("$", 3)[-1]
        return hmac.compare_digest(expected, digest64)
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session_token(user_id: str) -> str:
    expires_epoch = int(time.time()) + 60 * 60 * 24 * 30
    expires_iso = datetime.fromtimestamp(expires_epoch, timezone.utc).isoformat()
    session_id = secrets.token_urlsafe(18)
    payload = f"{session_id}.{user_id}.{expires_epoch}"
    signature = hmac.new(settings.jwt_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}.{signature}".encode()).decode()
    db.create_session(session_id, user_id, _token_hash(token), expires_iso)
    return token


def read_session_token(token: str) -> str | None:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        parts = raw.split(".")
        if len(parts) == 4:
            session_id, user_id, expires, signature = parts
            payload = f"{session_id}.{user_id}.{expires}"
            expected = hmac.new(settings.jwt_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected) or int(expires) < int(time.time()):
                return None
            if not db.session_is_active(session_id, user_id, _token_hash(token), datetime.now(timezone.utc).isoformat()):
                return None
            return user_id
        if len(parts) == 3:
            # Compatibilité temporaire avec les jetons créés avant la table sessions.
            user_id, expires, signature = parts
            payload = f"{user_id}.{expires}"
            expected = hmac.new(settings.jwt_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if hmac.compare_digest(signature, expected) and int(expires) >= int(time.time()):
                return user_id
    except (ValueError, TypeError, UnicodeDecodeError):
        return None
    return None


def revoke_session_token(token: str) -> bool:
    return db.revoke_session(_token_hash(token))
