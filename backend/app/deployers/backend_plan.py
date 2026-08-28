from __future__ import annotations

from pathlib import Path
from typing import Any

from .detect import detect_project
from .vercel import collect_files


def prepare_backend_plan(workspace: Path, project_name: str) -> dict[str, Any]:
    project = detect_project(workspace)
    if project["type"] not in {"python_backend", "node_backend", "docker"}:
        raise ValueError(f"Backend plan does not support detected project type: {project['type']}")
    files = collect_files(workspace)
    if project["type"] == "docker":
        build = "docker build -t <image> ."
        start = "docker run --rm -p <port>:<port> <image>"
        health = None
    elif project["type"] == "python_backend":
        build = "python -m compileall ."
        start = "uvicorn app:app --host 0.0.0.0 --port $PORT" if (workspace / "app.py").is_file() else "python main.py"
        health = "/health"
    else:
        build = "npm ci && npm run build" if project.get("build_command") else "npm ci"
        start = "npm start"
        health = "/health"
    return {
        "project_name": project_name.strip() or "assane-backend",
        "project": project,
        "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files),
        "build_command": build,
        "start_command": start,
        "health_path": health,
        "status": "preflight_only",
        "deployable": False,
        "warnings": [
            "No generic host adapter is installed. Configure a dedicated deployment gateway or an approved hosting target.",
            "Environment variables, database migrations, persistent storage, TLS, logs and rollback must be configured before production.",
        ],
    }
