from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from ..core.config import settings
from ..storage import db
from .sms_provider import get_sms_provider


def _hash_code(request_id: str, code: str) -> str:
    value = f"{request_id}:{code}:{settings.jwt_secret}".encode()
    return hashlib.sha256(value).hexdigest()


def mask_phone(phone: str) -> str:
    clean = phone.strip()
    if len(clean) <= 4:
        return "••••"
    return f"{clean[:3]}{'•' * max(2, len(clean) - 5)}{clean[-2:]}"


def create_and_send(phone: str, purpose: str, pending_id: str | None = None, user_id: str | None = None) -> dict[str, Any]:
    normalized = phone.strip()
    db.invalidate_active_otps(normalized, purpose)
    request_id = secrets.token_urlsafe(24)
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=settings.otp_expiry_seconds)).isoformat()
    db.create_otp_request(
        request_id=request_id,
        user_id=user_id,
        pending_id=pending_id,
        phone_number=normalized,
        code_hash=_hash_code(request_id, code),
        purpose=purpose,
        expires_at=expires_at,
        max_attempts=settings.otp_max_attempts,
    )
    provider = get_sms_provider()
    provider.send_sms(normalized, f"ASSANE AI : votre code de vérification est {code}. Il expire dans {settings.otp_expiry_seconds // 60} minutes.")
    return {"otp_request_id": request_id, "phone": mask_phone(normalized), "expires_at": expires_at, "retry_after_seconds": settings.otp_resend_cooldown_seconds}


def verify_code(request_id: str, code: str, purpose: str) -> dict[str, Any]:
    row = db.get_otp_request(request_id)
    if not row or row["purpose"] != purpose:
        return {"ok": False, "reason": "invalid"}
    if row["status"] != "pending":
        return {"ok": False, "reason": "used_or_expired"}
    if datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc):
        db.expire_otp(request_id)
        return {"ok": False, "reason": "expired"}
    if int(row["attempt_count"]) >= int(row["max_attempts"]):
        db.fail_otp(request_id)
        return {"ok": False, "reason": "too_many_attempts"}
    digest = _hash_code(request_id, code.strip())
    if not hmac.compare_digest(digest, row["code_hash"]):
        attempts = db.increment_otp_attempt(request_id)
        if attempts >= int(row["max_attempts"]):
            db.fail_otp(request_id)
            return {"ok": False, "reason": "too_many_attempts"}
        return {"ok": False, "reason": "invalid", "attempts_left": int(row["max_attempts"]) - attempts}
    db.verify_otp(request_id)
    return {"ok": True, "request": db.get_otp_request(request_id)}
