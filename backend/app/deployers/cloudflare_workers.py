from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from ..core.config import settings
from ..core.providers import ProviderError
from .detect import detect_project


ENTRYPOINTS = ("_worker.js", "worker.js", "src/index.js", "src/worker.js", "index.js")


def _config(script_name: str) -> tuple[str, str]:
    account = settings.cloudflare_account_id.strip()
    name = script_name.strip() or settings.cloudflare_worker_name.strip()
    if not account:
        raise ValueError("Missing configuration: CLOUDFLARE_ACCOUNT_ID")
    if not name or "/" in name or "\\" in name or len(name) > 100:
        raise ValueError("Invalid Cloudflare Worker name")
    return account, name


def _entrypoint(workspace: Path) -> Path:
    for name in ENTRYPOINTS:
        candidate = workspace / name
        if candidate.is_file():
            return candidate
    raise ValueError("No supported Cloudflare Worker entrypoint was detected")


def prepare_manifest(workspace: Path, script_name: str) -> dict[str, Any]:
    project = detect_project(workspace)
    account, name = _config(script_name)
    entrypoint = _entrypoint(workspace)
    if entrypoint.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Cloudflare Worker module exceeds the 25 MiB limit")
    return {
        "provider": "cloudflare_workers",
        "account_id": account,
        "script_name": name,
        "entrypoint": str(entrypoint.relative_to(workspace)),
        "project": project,
        "entrypoint_bytes": entrypoint.stat().st_size,
    }


def _headers() -> dict[str, str]:
    if not settings.cloudflare_token:
        raise ProviderError("Missing configuration: CLOUDFLARE_API_TOKEN")
    return {
        "Authorization": f"Bearer {settings.cloudflare_token}",
        "Content-Type": "application/javascript+module",
    }


def _script_url(account: str, script_name: str) -> str:
    base = settings.cloudflare_base_url.rstrip("/")
    return f"{base}/accounts/{quote(account, safe='')}/workers/scripts/{quote(script_name, safe='')}"


async def publish_worker(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("provider") != "cloudflare_workers":
        raise ValueError("Unsupported deployment provider")
    entrypoint = workspace / str(manifest.get("entrypoint", ""))
    if not entrypoint.is_file() or entrypoint.is_symlink():
        raise ValueError("Worker entrypoint is missing")
    if entrypoint.stat().st_size != manifest.get("entrypoint_bytes"):
        raise ValueError("Worker entrypoint changed after confirmation")
    account, name = _config(str(manifest.get("script_name", "")))
    content = entrypoint.read_bytes()
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        response = await client.put(_script_url(account, name), headers=_headers(), content=content)
        if response.status_code >= 400:
            raise ProviderError(f"Cloudflare Workers returned {response.status_code}: {response.text[:1000]}")
        payload = response.json() if response.content else {}
        if payload and payload.get("success") is False:
            raise ProviderError(f"Cloudflare Workers request failed: {payload.get('errors', [])}")

    live_url = settings.cloudflare_worker_url.strip()
    verified = False
    verification: dict[str, Any] = {"url": live_url or None, "reachable": False}
    if live_url:
        normalized = live_url if live_url.startswith(("http://", "https://")) else f"https://{live_url}"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                live_response = await client.get(normalized)
            verification = {"url": str(live_response.url), "http_status": live_response.status_code, "reachable": 200 <= live_response.status_code < 400}
            verified = verification["reachable"]
        except httpx.HTTPError as exc:
            verification = {"url": normalized, "reachable": False, "error": str(exc)}
    return {
        "ok": verified,
        "provider": "cloudflare_workers",
        "status": "READY" if verified else "ERROR",
        "deployment_id": name,
        "url": verification.get("url"),
        "verified": verified,
        "verification": verification,
        "error": None if verified else "Worker uploaded but its configured public URL was not verified",
    }
