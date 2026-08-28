from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.config import settings
from .detect import detect_project


ALLOWED_TRACKS = {"internal", "alpha", "beta", "production"}


def _aab_file(workspace: Path) -> Path:
    candidates = sorted(path for path in workspace.rglob("*.aab") if path.is_file() and not path.is_symlink())
    if not candidates:
        raise ValueError("No AAB found. Build bundleRelease before preparing Play Store publication.")
    return candidates[0]


def prepare_manifest(workspace: Path, project_name: str) -> dict[str, Any]:
    project = detect_project(workspace)
    if project.get("type") != "android":
        raise ValueError("Play Store publication requires an Android project")
    package_name = project_name.strip() or settings.google_play_package_name.strip()
    if not package_name or any(part == "" for part in package_name.split(".")):
        raise ValueError("Missing configuration: GOOGLE_PLAY_PACKAGE_NAME")
    track = settings.google_play_track.strip().lower()
    if track not in ALLOWED_TRACKS:
        raise ValueError("GOOGLE_PLAY_TRACK must be internal, alpha, beta or production")
    if not settings.google_play_service_account_json.strip():
        raise ValueError("Missing configuration: GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
    aab = _aab_file(workspace)
    return {
        "provider": "google_play",
        "package_name": package_name,
        "track": track,
        "aab_path": str(aab.relative_to(workspace)),
        "aab_bytes": aab.stat().st_size,
        "project": project,
        "status": "awaiting_confirmation",
        "release_commit_required": True,
    }


def _service():
    if not settings.google_play_service_account_json:
        raise ValueError("Missing Google Play service account configuration")
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Install google-api-python-client and google-auth on the backend") from exc
    credentials = service_account.Credentials.from_service_account_file(
        settings.google_play_service_account_json,
        scopes=["https://www.googleapis.com/auth/androidpublisher"],
    )
    return build("androidpublisher", "v3", credentials=credentials, cache_discovery=False)


def publish_aab(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("provider") != "google_play":
        raise ValueError("Unsupported Play Store manifest")
    aab = workspace / str(manifest.get("aab_path", ""))
    if not aab.is_file() or aab.is_symlink():
        raise ValueError("AAB file is missing")
    if aab.stat().st_size != manifest.get("aab_bytes"):
        raise ValueError("AAB changed after confirmation")
    package_name = str(manifest["package_name"])
    track = str(manifest["track"])
    service = _service()
    edit = service.edits().insert(body={}, packageName=package_name).execute()
    edit_id = edit["id"]
    with aab.open("rb") as stream:
        from googleapiclient.http import MediaFileUpload
        upload = MediaFileUpload(str(aab), mimetype="application/octet-stream", resumable=True)
        bundle = service.edits().bundles().upload(packageName=package_name, editId=edit_id, media_body=upload).execute()
    version_code = str(bundle["versionCode"])
    service.edits().tracks().update(
        packageName=package_name,
        editId=edit_id,
        track=track,
        body={"releases": [{"versionCodes": [version_code], "status": "completed"}]},
    ).execute()
    committed = service.edits().commit(packageName=package_name, editId=edit_id).execute()
    return {
        "ok": True,
        "verified": bool(committed),
        "provider": "google_play",
        "status": "READY" if committed else "ERROR",
        "deployment_id": edit_id,
        "url": f"https://play.google.com/store/apps/details?id={package_name}",
        "track": track,
        "version_code": version_code,
        "error": None if committed else "Play Store edit was not committed",
    }
