from __future__ import annotations

import asyncio
import hashlib
import re
import time
from pathlib import Path
from typing import Any

import httpx

from ..core.config import settings
from ..core.providers import ProviderError
from .detect import detect_project


MAX_FILES = 1_000
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
POLL_SECONDS = 4
POLL_TIMEOUT_SECONDS = 20 * 60


def _headers() -> dict[str, str]:
    if not settings.vercel_token:
        raise ProviderError("Missing configuration: VERCEL_TOKEN")
    return {"Authorization": f"Bearer {settings.vercel_token}"}


def normalize_project_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    if not normalized:
        raise ValueError("project_name must contain letters or numbers")
    return normalized[:80]


def _inside(workspace: Path, candidate: Path) -> bool:
    return candidate == workspace or workspace in candidate.parents


def collect_files(workspace: Path) -> list[dict[str, Any]]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError("Workspace not found")
    ignored = {".git", "node_modules", ".gradle", "build", "dist", "__pycache__", ".idea"}
    ignored_names = {".env", ".env.local", ".env.production", ".env.development", ".npmrc", "id_rsa", "id_ed25519"}
    files: list[dict[str, Any]] = []
    total = 0
    for candidate in sorted(workspace.rglob("*")):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        relative = candidate.relative_to(workspace)
        if any(part in ignored for part in relative.parts) or candidate.name in ignored_names or candidate.name.endswith((".pem", ".key", ".p12", ".keystore")):
            continue
        resolved = candidate.resolve()
        if not _inside(workspace, resolved):
            raise PermissionError("Workspace contains a file outside its root")
        size = candidate.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError(f"File too large for Vercel deployment: {relative}")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Workspace is too large for one Vercel deployment")
        sha1 = hashlib.sha1(candidate.read_bytes()).hexdigest()
        files.append({"file": relative.as_posix(), "sha": sha1, "size": size})
        if len(files) > MAX_FILES:
            raise ValueError("Too many files for one Vercel deployment")
    if not files:
        raise ValueError("Workspace is empty")
    return files


def prepare_manifest(workspace: Path, project_name: str) -> dict[str, Any]:
    project = detect_project(workspace)
    if project["type"] not in {"static", "frontend"}:
        raise ValueError(f"Vercel adapter does not support detected project type: {project['type']}")
    files = collect_files(workspace)
    return {
        "provider": "vercel",
        "project_name": normalize_project_name(project_name),
        "project": project,
        "files": files,
        "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files),
    }


def _query() -> dict[str, str]:
    return {"teamId": settings.vercel_team_id} if settings.vercel_team_id else {}


async def _upload_files(client: httpx.AsyncClient, workspace: Path, files: list[dict[str, Any]]) -> None:
    base = settings.vercel_base_url.rstrip("/")
    headers = _headers()
    for item in files:
        content = (workspace / item["file"]).read_bytes()
        upload_headers = {
            **headers,
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(content)),
            "x-Vercel-Digest": item["sha"],
        }
        response = await client.post(
            f"{base}/v2/files",
            params=_query(),
            headers=upload_headers,
            content=content,
        )
        if response.status_code >= 400:
            raise ProviderError(f"Vercel file upload returned {response.status_code}: {response.text[:500]}")


async def _create_deployment(client: httpx.AsyncClient, manifest: dict[str, Any]) -> dict[str, Any]:
    base = settings.vercel_base_url.rstrip("/")
    body = {
        "name": manifest["project_name"],
        "files": manifest["files"],
        "target": "production",
        "projectSettings": {"framework": None},
    }
    response = await client.post(
        f"{base}/v13/deployments",
        params={**_query(), "skipAutoDetectionConfirmation": "1"},
        headers={**_headers(), "Content-Type": "application/json"},
        json=body,
    )
    if response.status_code >= 400:
        raise ProviderError(f"Vercel deployment returned {response.status_code}: {response.text[:1000]}")
    return response.json()


async def _wait_for_ready(client: httpx.AsyncClient, deployment_id: str) -> dict[str, Any]:
    base = settings.vercel_base_url.rstrip("/")
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    latest: dict[str, Any] = {"id": deployment_id, "readyState": "QUEUED"}
    terminal = {"READY", "ERROR", "CANCELED", "CANCELLED"}
    while time.monotonic() < deadline:
        response = await client.get(
            f"{base}/v13/deployments/{deployment_id}",
            params=_query(),
            headers=_headers(),
        )
        if response.status_code >= 400:
            raise ProviderError(f"Vercel deployment status returned {response.status_code}: {response.text[:1000]}")
        latest = response.json()
        if latest.get("readyState") in terminal:
            return latest
        await asyncio.sleep(POLL_SECONDS)
    latest["readyState"] = "TIMEOUT"
    return latest


async def _verify_url(url: str) -> dict[str, Any]:
    normalized = url if url.startswith(("http://", "https://")) else f"https://{url}"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            response = await client.get(normalized)
        return {
            "url": str(response.url),
            "http_status": response.status_code,
            "reachable": 200 <= response.status_code < 400,
        }
    except httpx.HTTPError as exc:
        return {"url": normalized, "reachable": False, "error": str(exc)}


async def deploy_vercel(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("provider") != "vercel":
        raise ValueError("Unsupported deployment provider")
    if manifest.get("project", {}).get("type") not in {"static", "frontend"}:
        raise ValueError("Confirmed project type is not supported by the Vercel adapter")
    if normalize_project_name(manifest["project_name"]) != manifest["project_name"]:
        raise ValueError("Deployment project name changed after confirmation")
    current_files = collect_files(workspace)
    if current_files != manifest.get("files"):
        raise ValueError("Workspace changed after confirmation; deployment request must be recreated")
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        await _upload_files(client, workspace, manifest["files"])
        created = await _create_deployment(client, manifest)
        deployment_id = created.get("id")
        if not deployment_id:
            raise ProviderError("Vercel did not return a deployment id")
        latest = await _wait_for_ready(client, deployment_id)
    ready = latest.get("readyState") == "READY"
    raw_url = latest.get("url")
    if not raw_url and latest.get("alias"):
        raw_url = latest["alias"][0]
    verification = await _verify_url(raw_url) if ready and raw_url else {"reachable": False, "error": "No deployment URL returned"}
    return {
        "ok": ready and verification.get("reachable", False),
        "provider": "vercel",
        "status": latest.get("readyState"),
        "deployment_id": deployment_id,
        "url": verification.get("url") if verification.get("reachable") else raw_url,
        "verified": verification.get("reachable", False),
        "verification": verification,
        "error": latest.get("errorMessage") or latest.get("errorCode"),
    }
