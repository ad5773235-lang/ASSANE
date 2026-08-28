from __future__ import annotations

from typing import Any

from .registry import ToolSpec, registry


def save_workspace(task_id: str) -> dict[str, Any]:
    return {"ok": True, "task_id": task_id, "message": "Le workspace est persisté dans le stockage Assane AI."}


def download_artifact(artifact_id: str) -> dict[str, Any]:
    return {"ok": True, "artifact_id": artifact_id, "action": "download", "requires_client_request": True}


def share_artifact(artifact_id: str) -> dict[str, Any]:
    return {"ok": True, "artifact_id": artifact_id, "action": "share", "requires_client_request": True}


def deploy(task_id: str, target: str) -> dict[str, Any]:
    return {
        "ok": False,
        "implemented": False,
        "status": "not_implemented",
        "requires_confirmation": True,
        "action": "deploy",
        "target": target,
        "task_id": task_id,
        "message": "Demande enregistrée, mais aucun adaptateur de publication réel n’est encore installé pour cette cible.",
    }


def register_operations() -> None:
    registry.register(ToolSpec("save_workspace", "Enregistrer le workspace et ses checkpoints", frozenset({"workspace.write"}), True, save_workspace))
    registry.register(ToolSpec("download_artifact", "Préparer le téléchargement d’un artefact", frozenset({"artifact.read"}), False, download_artifact))
    registry.register(ToolSpec("share_artifact", "Préparer le partage contrôlé d’un artefact", frozenset({"artifact.share"}), True, share_artifact))
    registry.register(ToolSpec("deploy", "Demander un déploiement après confirmation", frozenset({"deployment.request"}), True, deploy))
