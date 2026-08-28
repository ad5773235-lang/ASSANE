from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.config import ROOT_DIR

SKILLS_DIR = ROOT_DIR / "backend" / "skills"


def load_skills() -> list[dict[str, Any]]:
    skills = []
    for manifest_path in SKILLS_DIR.glob("*/manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["directory"] = str(manifest_path.parent)
        skills.append(manifest)
    return skills


def select_skills(prompt: str) -> list[dict[str, Any]]:
    text = prompt.lower()
    selected = []
    for skill in load_skills():
        triggers = [str(item).lower() for item in skill.get("triggers", [])]
        if any(trigger in text for trigger in triggers):
            selected.append(skill)
    if not selected:
        selected = [skill for skill in load_skills() if skill.get("id") == "general-agent"]
    return selected
