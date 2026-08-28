from __future__ import annotations

import hashlib
import os

from pathlib import Path
from typing import Any

from ..core.config import settings
from ..storage import db
from ..storage.artifacts import save_artifact
from .registry import ToolSpec, registry


ALLOWED_PROGRAMS = {"python", "python3", "pytest", "gradle", "./gradlew", "git", "ls", "find"}


def workspace_for(task_id: str) -> Path:
    path = settings.data_dir / "workspaces" / task_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_path(workspace: Path, requested: str) -> Path:
    candidate = (workspace / requested).resolve()
    if candidate != workspace and workspace not in candidate.parents:
        raise PermissionError("Path outside workspace")
    return candidate


def list_files(task_id: str, depth: int = 3) -> dict[str, Any]:
    workspace = workspace_for(task_id)
    paths = []
    for path in workspace.rglob("*"):
        if path.is_file() and len(path.relative_to(workspace).parts) <= depth:
            paths.append(str(path.relative_to(workspace)))
    return {"ok": True, "files": sorted(paths)}


def read_file(task_id: str, path: str, max_chars: int = 100_000) -> dict[str, Any]:
    workspace = workspace_for(task_id)
    target = safe_path(workspace, path)
    if not target.is_file():
        return {"ok": False, "error": "file_not_found", "path": path}
    content = target.read_text(encoding="utf-8", errors="replace")
    return {"ok": True, "path": path, "content": content[:max_chars], "truncated": len(content) > max_chars}


def write_file(task_id: str, path: str, content: str) -> dict[str, Any]:
    workspace = workspace_for(task_id)
    target = safe_path(workspace, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path, "bytes": target.stat().st_size}


def run_command(task_id: str, program: str, args: list[str], timeout_seconds: int = 120) -> dict[str, Any]:
    if program not in ALLOWED_PROGRAMS:
        return {"ok": False, "error": "program_not_allowed", "program": program}
    from ..runners.manager import runner_manager
    return runner_manager.execute(task_id, program, args, timeout_seconds)


def _register_android_artifact(task_id: str, result: dict[str, Any], suffix: str, mime_type: str) -> dict[str, Any]:
    if not result.get("ok"):
        return result
    workspace = workspace_for(task_id).resolve()
    candidates = sorted(
        path for path in workspace.rglob(f"*.{suffix}")
        if path.is_file() and not path.is_symlink() and workspace in path.resolve().parents
    )
    task = db.get_task_internal(task_id)
    if candidates and task and task.get("user_id"):
        artifact_path = candidates[0]
        artifact = save_artifact(task["user_id"], task_id, artifact_path.name, artifact_path.read_bytes(), mime_type)
        result["artifact"] = artifact
    else:
        result["artifact_warning"] = f"Build succeeded but no .{suffix} was found to register."
    return result


def build_android_artifact(task_id: str, package_format: str = "apk", variant: str = "debug") -> dict[str, Any]:
    if package_format not in {"apk", "aab"}:
        return {"ok": False, "error": "invalid_package_format"}
    if package_format == "aab":
        if variant != "release":
            return {"ok": False, "error": "aab_requires_release_variant"}
        result = run_command(task_id, "./gradlew", ["bundleRelease"], 1200)
        return _register_android_artifact(task_id, result, "aab", "application/vnd.android.package-archive")
    result = run_command(task_id, "./gradlew", [f"assemble{variant.capitalize()}"], 1200)
    return _register_android_artifact(task_id, result, "apk", "application/vnd.android.package-archive")


def build_apk(task_id: str, variant: str = "debug") -> dict[str, Any]:
    if variant not in {"debug", "release"}:
        return {"ok": False, "error": "invalid_variant"}
    result = run_command(task_id, "./gradlew", [f"assemble{variant.capitalize()}"], 1200)
    return _register_android_artifact(task_id, result, "apk", "application/vnd.android.package-archive")


def run_android_tests(task_id: str) -> dict[str, Any]:
    args = ["test"]
    if settings.android_connected_tests:
        args.append("connectedDebugAndroidTest")
    result = run_command(task_id, "./gradlew", args, 1200)
    if result.get("ok") and not settings.android_connected_tests:
        result["note"] = "Unit tests executed; connected Android tests require ASSANE_ANDROID_CONNECTED_TESTS=true and an available emulator."
    return result


def register_local_tools() -> None:
    registry.register(ToolSpec("list_files", "Lister les fichiers du workspace", frozenset({"workspace.read"}), False, list_files))
    registry.register(ToolSpec("read_file", "Lire un fichier du workspace", frozenset({"workspace.read"}), False, read_file))
    registry.register(ToolSpec("write_file", "Écrire un fichier du workspace", frozenset({"workspace.write"}), True, write_file))
    registry.register(ToolSpec("run_command", "Lancer une commande autorisée dans le runner", frozenset({"sandbox.exec"}), True, run_command))
    registry.register(ToolSpec("build_apk", "Compiler un APK Android dans le runner", frozenset({"android.build"}), True, build_apk))
    registry.register(ToolSpec("build_android_artifact", "Produire un APK ou un AAB Android dans le runner", frozenset({"android.build"}), True, build_android_artifact))
    registry.register(ToolSpec("run_android_tests", "Lancer les tests Android dans le runner", frozenset({"android.emulator"}), True, run_android_tests))
