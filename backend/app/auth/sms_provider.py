from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import secrets
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

from ..core.config import settings

logger = logging.getLogger("assane_ai.sms")


class SmsProvider(ABC):
    @abstractmethod
    def send_sms(self, destination: str, message: str) -> None:
        raise NotImplementedError


class DevelopmentSmsProvider(SmsProvider):
    def send_sms(self, destination: str, message: str) -> None:
        # Le code n’est jamais renvoyé par l’API. Il apparaît uniquement dans les logs
        # locaux lorsque le mode de développement l’autorise.
        if settings.sms_log_otp:
            logger.warning("OTP SMS de développement pour %s : %s", destination, message)
        else:
            logger.info("OTP SMS de développement préparé pour %s", destination)


class ConfiguredHttpSmsProvider(SmsProvider):
    def send_sms(self, destination: str, message: str) -> None:
        raise RuntimeError("Le fournisseur SMS HTTP est déclaré mais son adaptateur réel n’est pas configuré")


class UnimatrixSmsProvider(SmsProvider):
    """Envoie le texte OTP généré localement par Assane via Unimatrix.

    Le code reste généré, haché et vérifié par Assane AI. Unimatrix sert ici de
    transport SMS ; il ne reçoit donc jamais le hash ni l’identifiant de session.
    """

    action = "sms.message.send"

    def _query_params(self) -> dict[str, str]:
        params = {
            "action": self.action,
            "accessKeyId": settings.unimatrix_access_key_id,
        }
        if settings.unimatrix_auth_mode == "hmac":
            params.update(
                {
                    "algorithm": "hmac-sha256",
                    "timestamp": str(int(time.time() * 1000)),
                    "nonce": secrets.token_urlsafe(16),
                }
            )
            canonical = "&".join(f"{key}={params[key]}" for key in sorted(params))
            digest = hmac.new(
                settings.unimatrix_access_key_secret.encode("utf-8"),
                canonical.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            params["signature"] = base64.b64encode(digest).decode("ascii")
        return params

    def send_sms(self, destination: str, message: str) -> None:
        if not settings.unimatrix_access_key_id:
            raise RuntimeError("UNIMATRIX_ACCESS_KEY_ID n’est pas configuré")
        if settings.unimatrix_auth_mode not in {"simple", "hmac"}:
            raise RuntimeError("UNIMATRIX_AUTH_MODE doit être simple ou hmac")
        if settings.unimatrix_auth_mode == "hmac" and not settings.unimatrix_access_key_secret:
            raise RuntimeError("UNIMATRIX_ACCESS_KEY_SECRET est obligatoire en mode HMAC")

        endpoint = settings.unimatrix_base_url.rstrip("/") + "/"
        payload: dict[str, Any] = {"to": destination, "text": message}
        try:
            with httpx.Client(timeout=settings.unimatrix_timeout_seconds) as client:
                response = client.post(endpoint, params=self._query_params(), json=payload)
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.error("Échec de l’envoi SMS Unimatrix", exc_info=exc)
            raise RuntimeError("Le service SMS Unimatrix est momentanément indisponible") from exc

        provider_code = str(result.get("code", ""))
        if provider_code != "0":
            # Ne pas copier la réponse complète : elle peut contenir des données
            # opérationnelles inutiles ou des informations sensibles du fournisseur.
            provider_message = str(result.get("message", "erreur fournisseur"))[:160]
            raise RuntimeError(f"Unimatrix a refusé l’envoi SMS : {provider_message}")

        logger.info("SMS OTP accepté par Unimatrix pour le numéro masqué")


def get_sms_provider() -> SmsProvider:
    if settings.sms_provider == "development":
        return DevelopmentSmsProvider()
    if settings.sms_provider == "http":
        return ConfiguredHttpSmsProvider()
    if settings.sms_provider == "unimatrix":
        return UnimatrixSmsProvider()
    raise RuntimeError("ASSANE_SMS_PROVIDER doit être development, unimatrix ou http")


__all__ = [
    "SmsProvider",
    "DevelopmentSmsProvider",
    "ConfiguredHttpSmsProvider",
    "UnimatrixSmsProvider",
    "get_sms_provider",
]

