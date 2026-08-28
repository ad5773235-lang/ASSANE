from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("ASSANE_ENV", "development")
    host: str = os.getenv("ASSANE_HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", os.getenv("ASSANE_PORT", "8000")))
    data_dir: Path = Path(os.getenv("ASSANE_DATA_DIR", str(ROOT_DIR / "backend")))
    database_url: str = os.getenv("ASSANE_DATABASE_URL", "sqlite:///" + str(ROOT_DIR / "backend" / "assane.db"))
    jwt_secret: str = os.getenv("ASSANE_JWT_SECRET", "change-me")
    owner_name: str = os.getenv("ASSANE_OWNER_NAME", "Assane Moussa Goudiaby")
    owner_birth_date: str = os.getenv("ASSANE_OWNER_BIRTH_DATE", "22/10/2008")
    owner_location: str = os.getenv("ASSANE_OWNER_LOCATION", "Sénégal, région de Dakar, département de Keur Massar, ville de Plan Jaxaay")
    cors_origins: str = os.getenv("ASSANE_CORS_ORIGINS", "*")
    public_base_url: str = os.getenv("ASSANE_PUBLIC_BASE_URL", "http://localhost:8000")
    manus_api_key: str = os.getenv("MANUS_API_KEY", "")
    manus_base_url: str = os.getenv("MANUS_API_BASE_URL", "https://open.manus.ai")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_owner: str = os.getenv("GITHUB_OWNER", "")
    github_repository: str = os.getenv("GITHUB_REPOSITORY", "")
    github_branch: str = os.getenv("GITHUB_BRANCH", "main")
    github_base_url: str = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "")
    mistral_base_url: str = os.getenv("MISTRAL_API_BASE_URL", "https://api.mistral.ai")
    mistral_model: str = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    vercel_token: str = os.getenv("VERCEL_TOKEN", "")
    vercel_team_id: str = os.getenv("VERCEL_TEAM_ID", "")
    vercel_base_url: str = os.getenv("VERCEL_API_BASE_URL", "https://api.vercel.com")
    cloudflare_token: str = os.getenv("CLOUDFLARE_API_TOKEN", "")
    cloudflare_account_id: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    cloudflare_pages_project: str = os.getenv("CLOUDFLARE_PAGES_PROJECT", "")
    cloudflare_pages_branch: str = os.getenv("CLOUDFLARE_PAGES_BRANCH", "main")
    cloudflare_worker_name: str = os.getenv("CLOUDFLARE_WORKER_NAME", "")
    cloudflare_worker_url: str = os.getenv("CLOUDFLARE_WORKER_URL", "")
    cloudflare_base_url: str = os.getenv("CLOUDFLARE_API_BASE_URL", "https://api.cloudflare.com/client/v4")
    google_play_package_name: str = os.getenv("GOOGLE_PLAY_PACKAGE_NAME", "")
    google_play_service_account_json: str = os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
    google_play_track: str = os.getenv("GOOGLE_PLAY_TRACK", "internal")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    openai_text_model: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
    openai_image_model: str = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    openai_audio_model: str = os.getenv("OPENAI_AUDIO_MODEL", "gpt-4o-mini-tts")
    stability_api_key: str = os.getenv("STABILITY_API_KEY", "")
    stability_base_url: str = os.getenv("STABILITY_API_BASE_URL", "https://api.stability.ai")
    deepgram_api_key: str = os.getenv("DEEPGRAM_API_KEY", "")
    deepgram_base_url: str = os.getenv("DEEPGRAM_API_BASE_URL", "https://api.deepgram.com")
    runner_mode: str = os.getenv("ASSANE_RUNNER_MODE", "local")
    docker_image: str = os.getenv("ASSANE_DOCKER_IMAGE", "assane/android-builder:2026-08")
    android_connected_tests: bool = os.getenv("ASSANE_ANDROID_CONNECTED_TESTS", "false").lower() == "true"
    max_iterations: int = int(os.getenv("ASSANE_MAX_ITERATIONS", "24"))
    task_timeout_seconds: int = int(os.getenv("ASSANE_TASK_TIMEOUT_SECONDS", "1200"))
    max_upload_bytes: int = int(os.getenv("ASSANE_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
    max_user_storage_bytes: int = int(os.getenv("ASSANE_MAX_USER_STORAGE_BYTES", str(500 * 1024 * 1024)))
    max_preview_bytes: int = int(os.getenv("ASSANE_MAX_PREVIEW_BYTES", str(250 * 1024 * 1024)))
    otp_expiry_seconds: int = int(os.getenv("ASSANE_OTP_EXPIRY_SECONDS", "300"))
    otp_max_attempts: int = int(os.getenv("ASSANE_OTP_MAX_ATTEMPTS", "5"))
    otp_resend_cooldown_seconds: int = int(os.getenv("ASSANE_OTP_RESEND_COOLDOWN_SECONDS", "60"))
    otp_max_requests_per_hour: int = int(os.getenv("ASSANE_OTP_MAX_REQUESTS_PER_HOUR", "5"))
    sms_provider: str = os.getenv("ASSANE_SMS_PROVIDER", "development")
    sms_log_otp: bool = os.getenv("ASSANE_SMS_LOG_OTP", "false").lower() == "true"
    sms_api_url: str = os.getenv("ASSANE_SMS_API_URL", "")
    sms_api_token: str = os.getenv("ASSANE_SMS_API_TOKEN", "")
    unimatrix_base_url: str = os.getenv("UNIMATRIX_BASE_URL", "https://api.unimtx.com")
    unimatrix_access_key_id: str = os.getenv("UNIMATRIX_ACCESS_KEY_ID", "")
    unimatrix_access_key_secret: str = os.getenv("UNIMATRIX_ACCESS_KEY_SECRET", "")
    unimatrix_auth_mode: str = os.getenv("UNIMATRIX_AUTH_MODE", "simple").lower()
    unimatrix_timeout_seconds: float = float(os.getenv("UNIMATRIX_TIMEOUT_SECONDS", "15"))

    def validate_production(self) -> None:
        if self.env.lower() in {"production", "prod"}:
            if not self.jwt_secret or self.jwt_secret in {"change-me", "secret", "dev-secret"}:
                raise RuntimeError("ASSANE_JWT_SECRET doit être défini avec une valeur aléatoire en production")
            if not self.public_base_url.lower().startswith("https://"):
                raise RuntimeError("ASSANE_PUBLIC_BASE_URL doit utiliser HTTPS en production")
            if self.cors_origins.strip() in {"", "*"}:
                raise RuntimeError("ASSANE_CORS_ORIGINS ne peut pas être '*' en production")
            if self.runner_mode == "local":
                raise RuntimeError("ASSANE_RUNNER_MODE=local est interdit en production; configurez Docker")
            if self.sms_provider == "development":
                raise RuntimeError("ASSANE_SMS_PROVIDER=development est interdit en production; configurez un fournisseur SMS réel")
            if self.sms_provider == "unimatrix":
                if not self.unimatrix_access_key_id:
                    raise RuntimeError("UNIMATRIX_ACCESS_KEY_ID est obligatoire avec ASSANE_SMS_PROVIDER=unimatrix")
                if self.unimatrix_auth_mode not in {"simple", "hmac"}:
                    raise RuntimeError("UNIMATRIX_AUTH_MODE doit être simple ou hmac")
                if self.unimatrix_auth_mode == "hmac" and not self.unimatrix_access_key_secret:
                    raise RuntimeError("UNIMATRIX_ACCESS_KEY_SECRET est obligatoire en mode HMAC Unimatrix")
                if not self.unimatrix_base_url.lower().startswith("https://"):
                    raise RuntimeError("UNIMATRIX_BASE_URL doit utiliser HTTPS")
            if self.sms_log_otp:
                raise RuntimeError("ASSANE_SMS_LOG_OTP=true est interdit en production")
            if self.otp_expiry_seconds <= 0 or self.otp_max_attempts <= 0 or self.otp_max_requests_per_hour <= 0:
                raise RuntimeError("Les limites OTP doivent être positives en production")


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
(settings.data_dir / "workspaces").mkdir(parents=True, exist_ok=True)
(settings.data_dir / "artifacts").mkdir(parents=True, exist_ok=True)
