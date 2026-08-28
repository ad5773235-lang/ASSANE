from __future__ import annotations

import asyncio
import ipaddress
import socket
import urllib.parse
from pathlib import Path
from typing import Any

from .inspect_tools import _public_url
from .local_tools import workspace_for
from .registry import ToolSpec, registry


async def browser_open(task_id: str, url: str, screenshot: bool = True) -> dict[str, Any]:
    if not _public_url(url):
        return {"ok": False, "error": "url_not_allowed"}
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"ok": False, "error": "playwright_not_installed", "detail": "Installez playwright puis exécutez playwright install chromium."}

    output_dir = workspace_for(task_id) / "browser"
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = output_dir / "page.png"
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1280, "height": 900})
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            title = await page.title()
            text = (await page.locator("body").inner_text())[:100_000]
            if screenshot:
                await page.screenshot(path=str(screenshot_path), full_page=True)
            final_url = page.url
            await browser.close()
        result: dict[str, Any] = {"ok": True, "url": final_url, "title": title, "text": text}
        if screenshot and screenshot_path.is_file():
            result["screenshot_path"] = str(screenshot_path.relative_to(workspace_for(task_id)))
        return result
    except Exception as exc:
        return {"ok": False, "error": "browser_failed", "detail": str(exc)}


def register_browser_tools() -> None:
    registry.register(
        ToolSpec(
            "browser_open",
            "Ouvrir et inspecter un site public dans le navigateur headless Assane",
            frozenset({"network.public.read", "workspace.write"}),
            False,
            browser_open,
        )
    )
