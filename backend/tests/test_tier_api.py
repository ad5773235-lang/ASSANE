from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import settings
from app.storage import db


class CapturingSms:
    messages: list[str] = []

    def send_sms(self, destination: str, message: str) -> None:
        self.messages.append(message)


@pytest.fixture()
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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


def test_authenticated_tier_routes(api_client: TestClient) -> None:
    registration = api_client.post(
        "/auth/register",
        json={
            "first_name": "A",
            "last_name": "Test",
            "email": "tier-api@example.test",
            "phone": "700000201",
            "password": "password-long",
        },
    )
    assert registration.status_code == 200
    code = registration.json()
    import re
    otp_code = re.search(r"\b(\d{6})\b", CapturingSms.messages[-1]).group(1)
    verified = api_client.post("/auth/register/verify", json={"otp_request_id": code["otp_request_id"], "code": otp_code})
    assert verified.status_code == 200
    token = verified.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    tiers = api_client.get("/tiers", headers=headers)
    assert tiers.status_code == 200
    assert tiers.json()["current"]["id"] == "assane_moyen"
    assert len(tiers.json()["tiers"]) == 3

    selected = api_client.put("/tier", headers=headers, json={"tier_id": "assane_eleve"})
    assert selected.status_code == 200
    assert selected.json()["tier"]["id"] == "assane_eleve"
    assert api_client.get("/tier", headers=headers).json()["tier"]["id"] == "assane_eleve"
    assert api_client.put("/tier", headers=headers, json={"tier_id": "unknown"}).status_code == 404


def test_task_history_is_scoped_to_authenticated_user(api_client: TestClient) -> None:
    import re

    def register_and_verify(email: str, phone: str) -> str:
        response = api_client.post(
            "/auth/register",
            json={
                "first_name": email.split("@")[0],
                "last_name": "History",
                "email": email,
                "phone": phone,
                "password": "password-long",
            },
        )
        assert response.status_code == 200
        otp_code = re.search(r"\b(\d{6})\b", CapturingSms.messages[-1]).group(1)
        verified = api_client.post(
            "/auth/register/verify",
            json={"otp_request_id": response.json()["otp_request_id"], "code": otp_code},
        )
        assert verified.status_code == 200
        return verified.json()["token"]

    token_a = register_and_verify("history-a@example.test", "700000301")
    token_b = register_and_verify("history-b@example.test", "700000302")
    created = api_client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"prompt": "Tâche privée du compte A"},
    )
    assert created.status_code == 200

    history_a = api_client.get("/tasks", headers={"Authorization": f"Bearer {token_a}"})
    history_b = api_client.get("/tasks", headers={"Authorization": f"Bearer {token_b}"})
    assert history_a.status_code == 200
    assert history_b.status_code == 200
    assert [task["prompt"] for task in history_a.json()["tasks"]] == ["Tâche privée du compte A"]
    assert history_b.json()["tasks"] == []
