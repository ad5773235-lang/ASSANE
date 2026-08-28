from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


DEPLOYMENT_STATES = {
    "awaiting_confirmation",
    "deploying",
    "succeeded",
    "failed",
    "expired",
    "cancelled",
}


@dataclass(frozen=True)
class DeploymentManifest:
    provider: str
    project_name: str
    files: list[dict[str, Any]]
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class DeploymentResult:
    ok: bool
    provider: str
    status: str
    deployment_id: str | None = None
    url: str | None = None
    verified: bool = False
    error: str | None = None
    details: dict[str, Any] | None = None


class DeploymentAdapter(Protocol):
    provider: str

    def prepare_manifest(self, workspace: Path, project_name: str) -> dict[str, Any]:
        """Return a serializable manifest without file contents or secrets."""

    async def deploy(self, workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
        """Deploy only after a separately persisted and confirmed request."""
