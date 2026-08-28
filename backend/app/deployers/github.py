from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from ..core.config import settings
from ..core.providers import ProviderError
from .detect import detect_project
from .vercel import collect_files


_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
MAX_FILES_PER_COMMIT = 1_000


def _repo_parts(value: str) -> tuple[str, str]:
    candidate = value.strip().removesuffix(".git").strip("/")
    if not candidate and settings.github_owner and settings.github_repository:
        candidate = f"{settings.github_owner}/{settings.github_repository}"
    if not _REPO_RE.fullmatch(candidate):
        raise ValueError("GitHub target must be an owner/repository pair")
    return tuple(candidate.split("/", 1))  # type: ignore[return-value]


def prepare_manifest(workspace: Path, repository: str) -> dict[str, Any]:
    owner, repo = _repo_parts(repository)
    files = collect_files(workspace)
    if len(files) > MAX_FILES_PER_COMMIT:
        raise ValueError("Too many files for one GitHub commit")
    return {
        "provider": "github",
        "owner": owner,
        "repository": repo,
        "branch": settings.github_branch,
        "project": detect_project(workspace),
        "files": files,
        "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files),
    }


def _headers() -> dict[str, str]:
    if not settings.github_token:
        raise ProviderError("Missing configuration: GITHUB_TOKEN")
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.github_token}",
        "X-GitHub-Api-Version": "2026-03-10",
        "Content-Type": "application/json",
    }


def _api_url(owner: str, repo: str, suffix: str) -> str:
    return f"{settings.github_base_url.rstrip('/')}/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/{suffix.lstrip('/')}"


async def _request(client: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    response = await client.request(method, url, headers=_headers(), **kwargs)
    if response.status_code >= 400:
        raise ProviderError(f"GitHub returned {response.status_code}: {response.text[:1000]}")
    return response.json() if response.content else {}


async def publish_github(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("provider") != "github":
        raise ValueError("Unsupported deployment provider")
    owner = str(manifest.get("owner", ""))
    repo = str(manifest.get("repository", ""))
    branch = str(manifest.get("branch", ""))
    if not owner or not repo or not branch:
        raise ValueError("GitHub manifest is incomplete")
    current_files = collect_files(workspace)
    if current_files != manifest.get("files"):
        raise ValueError("Workspace changed after confirmation; publication request must be recreated")
    ref_path = f"git/ref/heads/{quote(branch, safe='') }"
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        ref = await _request(client, "GET", _api_url(owner, repo, ref_path))
        head_sha = ref.get("object", {}).get("sha")
        if not head_sha:
            raise ProviderError("GitHub branch did not return a head SHA")
        commit = await _request(client, "GET", _api_url(owner, repo, f"git/commits/{head_sha}"))
        base_tree = commit.get("tree", {}).get("sha")
        if not base_tree:
            raise ProviderError("GitHub commit did not return a tree SHA")

        tree_entries = []
        for item in manifest["files"]:
            content = (workspace / item["file"]).read_bytes()
            blob = await _request(
                client,
                "POST",
                _api_url(owner, repo, "git/blobs"),
                json={"content": base64.b64encode(content).decode("ascii"), "encoding": "base64"},
            )
            blob_sha = blob.get("sha")
            if not blob_sha:
                raise ProviderError("GitHub blob creation did not return a SHA")
            tree_entries.append({"path": item["file"], "mode": "100644", "type": "blob", "sha": blob_sha})

        tree = await _request(
            client,
            "POST",
            _api_url(owner, repo, "git/trees"),
            json={"base_tree": base_tree, "tree": tree_entries},
        )
        tree_sha = tree.get("sha")
        if not tree_sha:
            raise ProviderError("GitHub tree creation did not return a SHA")
        created_commit = await _request(
            client,
            "POST",
            _api_url(owner, repo, "git/commits"),
            json={
                "message": f"Publish {manifest.get('project', {}).get('type', 'project')} via Assane AI",
                "tree": tree_sha,
                "parents": [head_sha],
            },
        )
        commit_sha = created_commit.get("sha")
        if not commit_sha:
            raise ProviderError("GitHub commit creation did not return a SHA")
        await _request(
            client,
            "PATCH",
            _api_url(owner, repo, f"git/refs/heads/{quote(branch, safe='')}"),
            json={"sha": commit_sha, "force": False},
        )
        verified_ref = await _request(client, "GET", _api_url(owner, repo, ref_path))
        verified_sha = verified_ref.get("object", {}).get("sha")

    verified = verified_sha == commit_sha
    return {
        "ok": verified,
        "provider": "github",
        "status": "READY" if verified else "ERROR",
        "deployment_id": commit_sha,
        "url": f"https://github.com/{owner}/{repo}/tree/{quote(branch, safe='')}",
        "verified": verified,
        "error": None if verified else "GitHub branch verification failed",
        "details": {"owner": owner, "repository": repo, "branch": branch, "commit_sha": commit_sha},
    }
