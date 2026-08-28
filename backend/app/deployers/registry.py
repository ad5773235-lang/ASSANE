from __future__ import annotations

from typing import Any

from .cloudflare import prepare_manifest as prepare_cloudflare_manifest, publish_pages
from .cloudflare_workers import prepare_manifest as prepare_worker_manifest, publish_worker
from .github import prepare_manifest as prepare_github_manifest, publish_github
from .google_play import prepare_manifest as prepare_google_play_manifest, publish_aab
from .vercel import deploy_vercel, prepare_manifest


ADAPTERS = {
    "vercel": {
        "provider": "vercel",
        "prepare_manifest": prepare_manifest,
        "deploy": deploy_vercel,
        "status": "available",
    },
    "github": {
        "provider": "github",
        "prepare_manifest": prepare_github_manifest,
        "deploy": publish_github,
        "status": "available",
    },
    "google_play": {
        "provider": "google_play",
        "prepare_manifest": prepare_google_play_manifest,
        "deploy": publish_aab,
        "status": "available",
    },
    "cloudflare_pages": {
        "provider": "cloudflare_pages",
        "prepare_manifest": prepare_cloudflare_manifest,
        "deploy": publish_pages,
        "status": "available",
    },
    "cloudflare_workers": {
        "provider": "cloudflare_workers",
        "prepare_manifest": prepare_worker_manifest,
        "deploy": publish_worker,
        "status": "available",
    },
}


def available_targets() -> list[dict[str, str]]:
    return [
        {"target": name, "status": adapter["status"]}
        for name, adapter in sorted(ADAPTERS.items())
    ]


def get_adapter(target: str) -> dict[str, Any] | None:
    return ADAPTERS.get(target.strip().lower())
