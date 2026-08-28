from __future__ import annotations

import hashlib
import ipaddress
import mimetypes
import socket
import urllib.parse
import zipfile
from pathlib import Path
from typing import Any

import httpx

from ..core.config import settings
from .local_tools import safe_path, workspace_for
from .registry import ToolSpec, registry


def _public_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        addresses = socket.getaddrinfo(parsed.hostname, None)
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError):
        return False
    return True


def inspect_url(url: str, max_bytes: int = 2_000_000) -> dict[str, Any]:
    if not _public_url(url):
        return {"ok": False, "error": "url_not_allowed"}
    try:
        response = httpx.get(url, follow_redirects=False, timeout=20, headers={"User-Agent": "AssaneAI/1.0"})
        content = response.content[:max_bytes]
        content_type = response.headers.get("content-type", "")
        text = content.decode("utf-8", errors="replace") if "text" in content_type or "json" in content_type else ""
        title = ""
        if "<title" in text.lower():
            lower = text.lower()
            start = lower.find("<title")
            start = lower.find(">", start) + 1
            end = lower.find("</title>", start)
            title = text[start:end].strip() if end > start else ""
        return {"ok": True, "url": url, "status_code": response.status_code, "content_type": content_type, "title": title, "text": text[:50_000]}
    except httpx.HTTPError as exc:
        return {"ok": False, "error": "fetch_failed", "detail": str(exc)}


def inspect_file(task_id: str, path: str) -> dict[str, Any]:
    workspace = workspace_for(task_id)
    target = safe_path(workspace, path)
    if not target.is_file():
        return {"ok": False, "error": "file_not_found", "path": path}
    data = target.read_bytes()
    mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    result: dict[str, Any] = {
        "ok": True,
        "path": path,
        "filename": target.name,
        "size_bytes": len(data),
        "mime_type": mime,
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    if target.suffix.lower() == ".apk":
        try:
            with zipfile.ZipFile(target) as archive:
                names = archive.namelist()
                result["apk"] = {
                    "valid_zip": True,
                    "has_android_manifest": "AndroidManifest.xml" in names,
                    "has_classes_dex": any(name.startswith("classes") and name.endswith(".dex") for name in names),
                    "entry_count": len(names),
                    "entries": names[:200],
                }
        except zipfile.BadZipFile:
            result["apk"] = {"valid_zip": False}
    elif mime.startswith("image/"):
        result["preview_url"] = f"/tasks/{task_id}/files/{urllib.parse.quote(path)}"
    elif target.suffix.lower() in {".txt", ".md", ".json", ".py", ".kt", ".java", ".xml", ".csv"}:
        result["text"] = data[:100_000].decode("utf-8", errors="replace")
    return result


def register_inspection_tools() -> None:
    registry.register(ToolSpec("inspect_url", "Inspecter un lien public sans accéder aux réseaux privés", frozenset({"network.public.read"}), False, inspect_url))
    registry.register(ToolSpec("inspect_file", "Inspecter un document, une image ou un APK dans le workspace", frozenset({"workspace.read"}), False, inspect_file))
