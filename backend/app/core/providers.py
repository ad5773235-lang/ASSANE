from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from .config import settings


class ProviderError(RuntimeError):
    pass


async def _request(method: str, url: str, *, headers: dict[str, str] | None = None,
                   json: Any | None = None, content: bytes | None = None,
                   data: dict[str, str] | None = None,
                   timeout: float = 60.0) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.request(method, url, headers=headers, json=json, content=content, data=data)
    if response.status_code >= 400:
        raise ProviderError(f"Provider returned {response.status_code}: {response.text[:1000]}")
    return response


def _require(value: str, name: str) -> str:
    if not value:
        raise ProviderError(f"Missing configuration: {name}")
    return value


async def manus_create_task(prompt: str, *, connectors: list[str] | None = None,
                            enable_skills: list[str] | None = None,
                            force_skills: list[str] | None = None) -> dict[str, Any]:
    key = _require(settings.manus_api_key, "MANUS_API_KEY")
    payload = {
        "message": {
            "content": [{"type": "text", "text": prompt}],
            "connectors": connectors or [],
            "enable_skills": enable_skills or [],
            "force_skills": force_skills or [],
            "task_references": [],
        }
    }
    response = await _request(
        "POST",
        f"{settings.manus_base_url.rstrip('/')}/v2/task.create",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    return response.json()


async def mistral_chat(messages: list[dict[str, str]]) -> dict[str, Any]:
    key = _require(settings.mistral_api_key, "MISTRAL_API_KEY")
    response = await _request(
        "POST",
        f"{settings.mistral_base_url.rstrip('/')}/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": settings.mistral_model, "messages": messages},
        timeout=120,
    )
    return response.json()


async def openai_chat(messages: list[dict[str, str]]) -> dict[str, Any]:
    key = _require(settings.openai_api_key, "OPENAI_API_KEY")
    response = await _request(
        "POST",
        f"{settings.openai_base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": settings.openai_text_model, "messages": messages},
        timeout=120,
    )
    return response.json()


async def openai_generate_image(prompt: str) -> dict[str, Any]:
    key = _require(settings.openai_api_key, "OPENAI_API_KEY")
    response = await _request(
        "POST",
        f"{settings.openai_base_url.rstrip('/')}/images/generations",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": settings.openai_image_model, "prompt": prompt, "size": "1024x1024"},
        timeout=180,
    )
    return response.json()


async def github_me() -> dict[str, Any]:
    key = _require(settings.github_token, "GITHUB_TOKEN")
    response = await _request(
        "GET",
        f"{settings.github_base_url.rstrip('/')}/user",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/vnd.github+json"},
        timeout=30,
    )
    return response.json()


async def vercel_projects() -> dict[str, Any]:
    key = _require(settings.vercel_token, "VERCEL_TOKEN")
    response = await _request(
        "GET",
        f"{settings.vercel_base_url.rstrip('/')}/v9/projects",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    return response.json()


async def cloudflare_verify_token() -> dict[str, Any]:
    key = _require(settings.cloudflare_token, "CLOUDFLARE_API_TOKEN")
    response = await _request(
        "GET",
        f"{settings.cloudflare_base_url.rstrip('/')}/user/tokens/verify",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    return response.json()


async def deepgram_transcribe(audio: bytes, mimetype: str = "audio/wav") -> dict[str, Any]:
    key = _require(settings.deepgram_api_key, "DEEPGRAM_API_KEY")
    response = await _request(
        "POST",
        f"{settings.deepgram_base_url.rstrip('/')}/v1/listen?model=nova-3&smart_format=true",
        headers={"Authorization": f"Token {key}", "Content-Type": mimetype},
        content=audio,
        timeout=180,
    )
    return response.json()


async def stability_generate_image(prompt: str, output: Path) -> Path:
    key = _require(settings.stability_api_key, "STABILITY_API_KEY")
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{settings.stability_base_url.rstrip('/')}/v2beta/stable-image/generate/core",
            headers={"Authorization": f"Bearer {key}", "Accept": "image/*"},
            data={"prompt": prompt, "output_format": "png"},
        )
    if response.status_code >= 400:
        raise ProviderError(f"Stability returned {response.status_code}: {response.text[:1000]}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(response.content)
    return output
