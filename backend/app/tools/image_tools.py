from __future__ import annotations

import base64
import io
import mimetypes
import urllib.parse
from pathlib import Path
from typing import Any

import httpx
from PIL import Image

from ..storage.artifacts import save_artifact
from .inspect_tools import _public_url
from .local_tools import workspace_for
from .registry import ToolSpec, registry

MAX_IMAGES = 12
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PREVIEW_BYTES = 180 * 1024


def _preview(data: bytes, content_type: str) -> str | None:
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.thumbnail((640, 640))
            if image.mode != "RGB":
                image = image.convert("RGB")
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=82, optimize=True)
        encoded = base64.b64encode(output.getvalue())
        if len(encoded) > MAX_PREVIEW_BYTES:
            return None
        return f"data:image/jpeg;base64,{encoded.decode('ascii')}"
    except (OSError, ValueError):
        return None


def _image_name(source_url: str, index: int) -> str:
    parsed = urllib.parse.urlparse(source_url)
    name = Path(parsed.path).name or f"image-{index}.bin"
    safe = "".join(char if char.isalnum() or char in {".", "-", "_"} else "_" for char in name)
    return safe[:120] or f"image-{index}.bin"


async def _download_image(client: httpx.AsyncClient, source_url: str) -> tuple[bytes, str, str] | None:
    if not _public_url(source_url):
        return None
    response = await client.get(source_url, follow_redirects=False, headers={"User-Agent": "AssaneAI/1.0"})
    if response.status_code in {301, 302, 303, 307, 308}:
        location = response.headers.get("location", "")
        redirected = urllib.parse.urljoin(source_url, location)
        if not _public_url(redirected):
            return None
        response = await client.get(redirected, follow_redirects=False, headers={"User-Agent": "AssaneAI/1.0"})
        source_url = redirected
    if response.status_code < 200 or response.status_code >= 300 or len(response.content) > MAX_IMAGE_BYTES:
        return None
    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
    if not content_type.startswith("image/"):
        guessed = mimetypes.guess_type(urllib.parse.urlparse(source_url).path)[0] or ""
        if not guessed.startswith("image/"):
            return None
        content_type = guessed
    if len(response.content) < 64:
        return None
    return response.content, content_type, source_url


async def extract_images(
    task_id: str,
    url: str,
    limit: int = 8,
    persist: bool = False,
    user_id: str | None = None,
) -> dict[str, Any]:
    if not _public_url(url):
        return {"ok": False, "error": "url_not_allowed"}
    limit = max(1, min(limit, MAX_IMAGES))
    if persist and not user_id:
        return {"ok": False, "error": "user_id_required_for_persistence"}
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"ok": False, "error": "playwright_not_installed"}

    candidates: list[dict[str, Any]] = []
    final_url = url
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1280, "height": 900})
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            final_url = page.url
            candidates = await page.locator("img").evaluate_all(
                """els => els.map(img => ({src: img.currentSrc || img.src, alt: img.alt || '', width: img.naturalWidth || 0, height: img.naturalHeight || 0}))"""
            )
            meta_images = await page.locator("meta[property='og:image'], meta[name='twitter:image']").evaluate_all(
                """els => els.map(meta => ({src: meta.content || '', alt: ''}))"""
            )
            candidates.extend(meta_images)
            await browser.close()
    except Exception as exc:
        return {"ok": False, "error": "browser_failed", "detail": str(exc)[:500]}

    seen: set[str] = set()
    images: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        for index, candidate in enumerate(candidates):
            raw = str(candidate.get("src", "")).strip()
            source_url = urllib.parse.urljoin(final_url, raw)
            source_url = source_url.split("#", 1)[0]
            if source_url in seen or not _public_url(source_url):
                continue
            seen.add(source_url)
            try:
                downloaded = await _download_image(client, source_url)
            except httpx.HTTPError:
                continue
            if not downloaded:
                continue
            content, content_type, resolved_url = downloaded
            item: dict[str, Any] = {
                "source_url": resolved_url,
                "alt": str(candidate.get("alt", ""))[:500],
                "mime_type": content_type,
                "size_bytes": len(content),
                "width": int(candidate.get("width", 0) or 0),
                "height": int(candidate.get("height", 0) or 0),
                "preview_data_url": _preview(content, content_type),
                "stored": False,
            }
            if persist:
                artifact = save_artifact(user_id, task_id, _image_name(resolved_url, index), content, content_type)
                item["artifact"] = artifact
                item["stored"] = True
                artifacts.append(artifact)
            images.append(item)
            if len(images) >= limit:
                break

    return {
        "ok": True,
        "url": final_url,
        "images": images,
        "count": len(images),
        "artifacts": artifacts,
        "persisted": persist,
    }


def register_image_tools() -> None:
    registry.register(
        ToolSpec(
            "extract_images",
            "Extraire les images publiques d’une page sans conserver d’artefact automatiquement",
            frozenset({"network.public.read"}),
            False,
            extract_images,
        )
    )
