from __future__ import annotations

import json
from pathlib import Path
from typing import Any


IGNORED_DIRS = {".git", ".gradle", "node_modules", "build", "dist", ".idea", "__pycache__"}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _has_file(workspace: Path, name: str) -> bool:
    return (workspace / name).is_file()


def detect_project(workspace: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError("Workspace not found")

    package = _read_json(workspace / "package.json") if _has_file(workspace, "package.json") else {}
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts", {}), dict) else {}
    dependencies = {
        str(name).lower()
        for group in ("dependencies", "devDependencies", "peerDependencies")
        for name in (package.get(group, {}) or {})
        if isinstance(package.get(group, {}), dict)
    }
    names = {path.name for path in workspace.iterdir()}
    has_gradle = any(name in names for name in ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"))
    has_docker = _has_file(workspace, "Dockerfile") or _has_file(workspace, "docker-compose.yml") or _has_file(workspace, "docker-compose.yaml")
    has_python = any(_has_file(workspace, name) for name in ("requirements.txt", "pyproject.toml", "Pipfile", "manage.py"))
    has_html = any(path.is_file() and path.suffix.lower() in {".html", ".htm"} for path in workspace.iterdir())
    frontend_markers = {"next", "nuxt", "vite", "react", "react-dom", "vue", "svelte", "astro", "@angular/core"}
    has_frontend_dependency = bool(dependencies & frontend_markers)
    has_build_script = isinstance(scripts.get("build"), str) and bool(scripts.get("build"))
    has_start_script = isinstance(scripts.get("start"), str) and bool(scripts.get("start"))

    if has_gradle or any(path.name.startswith("gradlew") for path in workspace.iterdir()):
        return {
            "type": "android",
            "runtime": "android",
            "framework": "gradle-kotlin" if _has_file(workspace, "build.gradle.kts") else "gradle",
            "build_command": "./gradlew assembleDebug",
            "test_command": "./gradlew test",
            "deployable_targets": ["artifact"],
            "warnings": ["Requires Android SDK, JDK and a configured build runner."],
        }
    if has_docker:
        return {
            "type": "docker",
            "runtime": "container",
            "framework": "docker",
            "build_command": "docker build .",
            "test_command": None,
            "deployable_targets": ["container_host"],
            "warnings": ["Requires an image registry and a container host; never exposes backend secrets to the build."],
        }
    if has_frontend_dependency or has_build_script:
        framework = next(iter(sorted(dependencies & frontend_markers)), "javascript-build")
        return {
            "type": "frontend",
            "runtime": "node",
            "framework": framework,
            "build_command": scripts.get("build") or "npm run build",
            "test_command": scripts.get("test"),
            "output_directory": "dist" if framework in {"vite", "vue", "svelte", "astro"} else ".next" if framework == "next" else None,
            "deployable_targets": ["vercel", "cloudflare_pages"],
            "warnings": [],
        }
    if has_python:
        return {
            "type": "python_backend",
            "runtime": "python",
            "framework": "django" if _has_file(workspace, "manage.py") else "python",
            "build_command": None,
            "test_command": "pytest" if _has_file(workspace, "pytest.ini") or _has_file(workspace, "pyproject.toml") else None,
            "deployable_targets": ["python_host"],
            "warnings": ["Needs a compatible Python host, secrets management, health checks and persistent storage policy."],
        }
    if has_start_script:
        return {
            "type": "node_backend",
            "runtime": "node",
            "framework": "node",
            "build_command": scripts.get("build"),
            "test_command": scripts.get("test"),
            "deployable_targets": ["node_host"],
            "warnings": ["Needs a compatible Node host, secrets management, health checks and persistent storage policy."],
        }
    if has_html:
        return {
            "type": "static",
            "runtime": "static",
            "framework": "html",
            "build_command": None,
            "test_command": None,
            "output_directory": ".",
            "deployable_targets": ["vercel", "cloudflare_pages"],
            "warnings": [],
        }
    return {
        "type": "unknown",
        "runtime": "unknown",
        "framework": None,
        "build_command": None,
        "test_command": None,
        "deployable_targets": [],
        "warnings": ["No supported project manifest was detected."],
    }
