from __future__ import annotations

import asyncio
import json
import mimetypes
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from ..core.config import settings
from ..core.providers import ProviderError
from .detect import detect_project
from .vercel import collect_files

POLL_SECONDS = 4
POLL_TIMEOUT_SECONDS = 20 * 60


def _account_and_project(value: str) -> tuple[str, str]:
    account = settings.cloudflare_account_id.strip()
    project = value.strip() or settings.cloudflare_pages_project.strip()
    if not account:
        raise ValueError("Missing configuration: CLOUDFLARE_ACCOUNT_ID")
    if not project:
        raise ValueError("Missing configuration: CLOUDFLARE_PAGES_PROJECT")
    if "/" in project or "\\" in project or len(project) > 100:
        raise ValueError("Invalid Cloudflare Pages project name")
    return account, project


def prepare_manifest(workspace: Path, project_name: str) -> dict[str, Any]:
    project = detect_project(workspace)
    if project["type"] not in {"static", "frontend"}:
        raise ValueError(f"Cloudflare Pages adapter does not support detected project type: {project['type']}")
    account, pages_project = _account_and_project(project_name)
    files = collect_files(workspace)
    return {
        "provider": "cloudflare_pages",
        "account_id": account,
        "project_name": pages_project,
        "branch": settings.cloudflare_pages_branch,
        "project": project,
        "files": files,
        "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files),
    }


def _headers() -> dict[str, str]:
    if not settings.cloudflare_token:
        raise ProviderError("Missing configuration: CLOUDFLARE_API_TOKEN")
    return {"Authorization": f"Bearer {settings.cloudflare_token}"}


def _url(account: str, project: str, suffix: str = "") -> str:
    base = settings.cloudflare_base_url.rstrip("/")
    return f"{base}/accounts/{quote(account, safe='')}/pages/projects/{quote(project, safe='')}/deployments{suffix}"


async def _request(client: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    response = await client.request(method, url, headers=_headers(), **kwargs)
    if response.status_code >= 400:
        raise ProviderError(f"Cloudflare returned {response.status_code}: {response.text[:1000]}")
    payload = response.json() if response.content else {}
    if not payload.get("success", True):
        raise ProviderError(f"Cloudflare request failed: {json.dumps(payload.get('errors', []))[:1000]}")
    return payload


async def publish_pages(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("provider") != "cloudflare_pages":
        raise ValueError("Unsupported deployment provider")
    current_files = collect_files(workspace)
    if current_files != manifest.get("files"):
        raise ValueError("Workspace changed after confirmation; publication request must be recreated")
    account = str(manifest["account_id"])
    project = str(manifest["project_name"])
    files = {}
    for item in manifest["files"]:
        path = workspace / item["file"]
        content = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        files[item["file"]] = (item["file"], content, content_type)
    multipart = [("file", value) for value in files.values()]
    multipart.append(("manifest", (None, json.dumps({item["file"]: item["sha"] for item in manifest["files"]}), "application/json")))
    multipart.append(("branch", (None, str(manifest.get("branch", settings.cloudflare_pages_branch)))))
    multipart.append(("commit_dirty", (None, "false")))
    multipart.append(("commit_message", (None, "Publish via Assane AI")))
    project_info = manifest.get("project", {})
    output_dir = project_info.get("output_directory")
    if output_dir:
        multipart.append(("pages_build_output_dir", (None, str(output_dir))))

    async with httpx.AsyncClient(timeout=180, follow_redirects=True) as client:
        created = await _request(client, "POST", _url(account, project), files=multipart)
        result = created.get("result") or {}
        deployment_id = result.get("id")
        if not deployment_id:
            raise ProviderError("Cloudflare did not return a deployment id")
        deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
        latest = result
        while time.monotonic() < deadline:
            latest_response = await _request(client, "GET", _url(account, project, f"/{quote(str(deployment_id), safe='')}"))
            latest = latest_response.get("result") or latest
            stage = (latest.get("latest_stage") or {}).get("status")
            if stage in {"success", "failure", "canceled"}:
                break
            await asyncio.sleep(POLL_SECONDS)

    stage_status = (latest.get("latest_stage") or {}).get("status")
    raw_url = latest.get("url") or ((latest.get("aliases") or [None])[0])
    verified = False
    verification: dict[str, Any] = {"url": raw_url, "reachable": False}
    if stage_status == "success" and raw_url:
        normalized = raw_url if str(raw_url).startswith(("http://", "https://")) else f"https://{raw_url}"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                response = await client.get(normalized)
            verification = {"url": str(response.url), "http_status": response.status_code, "reachable": 200 <= response.status_code < 400}
            verified = verification["reachable"]
        except httpx.HTTPError as exc:
            verification = {"url": normalized, "reachable": False, "error": str(exc)}
    return {
        "ok": stage_status == "success" and verified,
        "provider": "cloudflare_pages",
        "status": "READY" if stage_status == "success" and verified else "ERROR",
        "deployment_id": deployment_id,
        "url": verification.get("url") if verified else raw_url,
        "verified": verified,
        "verification": verification,
        "error": None if stage_status == "success" and verified else f"Cloudflare stage={stage_status}, verified={verified}",
    }
