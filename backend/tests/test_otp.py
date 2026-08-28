from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import settings
from app.storage import db


class CapturingSms:
    messages: list[tuple[str, str]] = []

    def send_sms(self, destination: str, message: str) -> None:
        self.messages.append((destination, message))


@pytest.fixture()
def otp_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    original_data_dir = settings.data_dir
    object.__setattr__(settings, "data_dir", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "assane.db")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "artifacts").mkdir()
    CapturingSms.messages = []
    monkeypatch.setattr("app.auth.otp.get_sms_provider", lambda: CapturingSms())
    with TestClient(app) as client:
        yield client
    object.__setattr__(settings, "data_dir", original_data_dir)


def extract_code(message: str) -> str:
    match = re.search(r"\b(\d{6})\b", message)
    assert match
    return match.group(1)


def test_registration_requires_otp_and_activates_only_after_verification(otp_client: TestClient) -> None:
    response = otp_client.post(
        "/auth/register",
        json={
            "first_name": "A",
            "last_name": "Otp",
            "email": "otp@example.test",
            "phone": "+221700000301",
            "password": "password-long",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "otp_required"
    assert db.get_user_by_email("otp@example.test") is None
    assert len(CapturingSms.messages) == 1

    wrong = otp_client.post("/auth/register/verify", json={"otp_request_id": payload["otp_request_id"], "code": "123456"})
    assert wrong.status_code == 400
    assert db.get_user_by_email("otp@example.test") is None

    code = extract_code(CapturingSms.messages[-1][1])
    verified = otp_client.post("/auth/register/verify", json={"otp_request_id": payload["otp_request_id"], "code": code})
    assert verified.status_code == 200
    user = db.get_user_by_email("otp@example.test")
    assert user and bool(user["phone_verified"]) is True
    assert verified.json()["token"]

    reused = otp_client.post("/auth/register/verify", json={"otp_request_id": payload["otp_request_id"], "code": code})
    assert reused.status_code == 400


def test_resend_invalidates_previous_code(otp_client: TestClient) -> None:
    started = otp_client.post(
        "/auth/register",
        json={
            "first_name": "A",
            "last_name": "Resend",
            "email": "resend@example.test",
            "phone": "+221700000302",
            "password": "password-long",
        },
    ).json()
    old_code = extract_code(CapturingSms.messages[-1][1])
    resent = otp_client.post("/auth/register/resend", json={"pending_signup_id": started["pending_signup_id"]})
    assert resent.status_code == 200
    new_code = extract_code(CapturingSms.messages[-1][1])
    assert old_code != new_code
    assert otp_client.post("/auth/register/verify", json={"otp_request_id": started["otp_request_id"], "code": old_code}).status_code == 400
    assert otp_client.post("/auth/register/verify", json={"otp_request_id": resent.json()["otp_request_id"], "code": new_code}).status_code == 200
