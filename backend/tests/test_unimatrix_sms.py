from __future__ import annotations

import base64
import hashlib
import hmac

from app.auth import sms_provider
from app.auth.sms_provider import UnimatrixSmsProvider
from app.core.config import settings


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeClient:
    last_request: tuple[str, dict, dict] | None = None

    def __init__(self, *args, **kwargs):
        pass
    response_payload = {"code": "0", "message": "Success", "data": {"id": "message-id"}}

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def post(self, endpoint: str, *, params: dict, json: dict) -> FakeResponse:
        FakeClient.last_request = (endpoint, params, json)
        return FakeResponse(FakeClient.response_payload)


def _set_setting(name: str, value):
    original = getattr(settings, name)
    object.__setattr__(settings, name, value)
    return original


def test_unimatrix_simple_mode_sends_expected_payload(monkeypatch):
    originals = {
        "sms_provider": _set_setting("sms_provider", "unimatrix"),
        "unimatrix_access_key_id": _set_setting("unimatrix_access_key_id", "test-access-id"),
        "unimatrix_auth_mode": _set_setting("unimatrix_auth_mode", "simple"),
        "unimatrix_base_url": _set_setting("unimatrix_base_url", "https://api.unimtx.test"),
    }
    try:
        monkeypatch.setattr(sms_provider.httpx, "Client", FakeClient)
        FakeClient.last_request = None
        UnimatrixSmsProvider().send_sms("+221770000000", "ASSANE AI : code 123456")
        endpoint, params, payload = FakeClient.last_request
        assert endpoint == "https://api.unimtx.test/"
        assert params == {"action": "sms.message.send", "accessKeyId": "test-access-id"}
        assert payload == {"to": "+221770000000", "text": "ASSANE AI : code 123456"}
    finally:
        for name, value in originals.items():
            object.__setattr__(settings, name, value)


def test_unimatrix_hmac_signature_is_deterministic_for_captured_query(monkeypatch):
    originals = {
        "sms_provider": _set_setting("sms_provider", "unimatrix"),
        "unimatrix_access_key_id": _set_setting("unimatrix_access_key_id", "test-access-id"),
        "unimatrix_access_key_secret": _set_setting("unimatrix_access_key_secret", "test-secret"),
        "unimatrix_auth_mode": _set_setting("unimatrix_auth_mode", "hmac"),
        "unimatrix_base_url": _set_setting("unimatrix_base_url", "https://api.unimtx.test"),
    }
    try:
        monkeypatch.setattr(sms_provider.httpx, "Client", FakeClient)
        FakeClient.last_request = None
        provider = UnimatrixSmsProvider()
        params = provider._query_params()
        signature = params.pop("signature")
        canonical = "&".join(f"{key}={params[key]}" for key in sorted(params))
        expected = base64.b64encode(hmac.new(b"test-secret", canonical.encode(), hashlib.sha256).digest()).decode("ascii")
        assert params["action"] == "sms.message.send"
        assert params["accessKeyId"] == "test-access-id"
        assert params["algorithm"] == "hmac-sha256"
        assert signature == expected
    finally:
        for name, value in originals.items():
            object.__setattr__(settings, name, value)
