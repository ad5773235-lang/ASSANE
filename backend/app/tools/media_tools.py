from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.config import settings
from ..core.providers import openai_generate_image, stability_generate_image
from .registry import ToolSpec, registry


async def generate_image(prompt: str, provider: str = "openai") -> dict[str, Any]:
    if provider == "stability":
        output = settings.data_dir / "artifacts" / "generated" / "image.png"
        path = await stability_generate_image(prompt, output)
        return {"ok": True, "provider": "stability", "path": str(path)}
    result = await openai_generate_image(prompt)
    return {"ok": True, "provider": "openai", "response": result}


def register_media_tools() -> None:
    registry.register(ToolSpec("generate_image", "Générer une image avec un fournisseur configuré", frozenset({"media.generate"}), True, generate_image))
