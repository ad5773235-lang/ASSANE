from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core.auth import create_session_token, hash_password, read_session_token, revoke_session_token, verify_password
from ..auth.otp import create_and_send, verify_code
from ..core.config import settings
from ..deployers.backend_plan import prepare_backend_plan
from ..deployers.detect import detect_project
from ..deployers.registry import get_adapter
from ..deployers.vercel import normalize_project_name
from ..core.providers import (
    cloudflare_verify_token,
    github_me,
    manus_create_task,
    mistral_chat,
    openai_chat,
    vercel_projects,
)
from ..orchestrator.engine import run_task
from ..jobs.worker import PersistentWorker
from ..runners.manager import runner_manager
from ..preview import create_preview, resolve_preview, revoke_preview
from ..skills.loader import load_skills, select_skills
from ..storage import db
from ..tiers.config import TierConfig, get_tier, list_tiers, UNIVERSAL_LIMITATIONS
from ..storage.artifacts import get_artifact, save_artifact
from ..tools.inspect_tools import inspect_file, inspect_url, register_inspection_tools
from ..tools.image_tools import extract_images, register_image_tools
from ..tools.browser_tools import browser_open, register_browser_tools
from ..tools.local_tools import build_android_artifact, register_local_tools
from ..tools.media_tools import generate_image, register_media_tools
from ..tools.operations import register_operations

app = FastAPI(title="Assane AI Core", version="1.0.0")
_job_worker: PersistentWorker | None = None
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=5, max_length=254)
    phone: str = Field(min_length=5, max_length=30)
    password: str = Field(min_length=8, max_length=200)


class OtpVerifyRequest(BaseModel):
    otp_request_id: str = Field(min_length=8, max_length=200)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class OtpResendRequest(BaseModel):
    pending_signup_id: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)


class UrlInspectRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2_000)


class ImageExtractionRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2_000)
    task_id: str = "general"
    limit: int = Field(default=8, ge=1, le=12)
    save: bool = False


class FileInspectRequest(BaseModel):
    task_id: str
    path: str


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=10_000)
    provider: str = "openai"


class PreferencesRequest(BaseModel):
    theme: str = Field(default="dark", max_length=40)
    background: str = Field(default="default", max_length=80)
    custom_instructions: str = Field(default="", max_length=10_000)


class DeploymentRequest(BaseModel):
    target: str = Field(default="vercel", min_length=1, max_length=40)
    project_name: str = Field(min_length=1, max_length=100)


class AndroidBuildRequest(BaseModel):
    package_format: str = Field(default="apk", pattern="^(apk|aab)$")
    variant: str = Field(default="debug", pattern="^(debug|release)$")


class TierSelectionRequest(BaseModel):
    tier_id: str = Field(min_length=1, max_length=40)


def tier_for_user(user_id: str) -> TierConfig:
    try:
        return get_tier(db.get_user_tier(user_id))
    except ValueError:
        db.set_user_tier(user_id, "assane_moyen")
        return get_tier("assane_moyen")


def public_tier(cfg: TierConfig) -> dict:
    return {
        "id": cfg.id,
        "name": cfg.name,
        "description": cfg.description,
        "max_iterations": cfg.max_iterations,
        "task_timeout_seconds": cfg.task_timeout_seconds,
        "max_concurrent_tasks": cfg.max_concurrent_tasks,
        "runner_mode": cfg.runner_mode,
        "persistence": cfg.persistence,
        "deployment_targets": list(cfg.deployment_targets),
        "allow_android_release_build": cfg.allow_android_release_build,
        "allow_google_play_publish": cfg.allow_google_play_publish,
        "web_search_enabled": cfg.web_search_enabled,
        "image_generation_enabled": cfg.image_generation_enabled,
        "max_web_search_results": cfg.max_web_search_results,
        "max_images_per_request": cfg.max_images_per_request,
        "health_checks_enabled": cfg.health_checks_enabled,
        "rollback_enabled": cfg.rollback_enabled,
    }


def public_deployment(deployment: dict) -> dict:
    manifest = json.loads(deployment.get("manifest_json", "{}"))
    return {
        "id": deployment["id"],
        "task_id": deployment["task_id"],
        "target": deployment["target"],
        "project_name": deployment["project_name"],
        "status": deployment["status"],
        "provider_id": deployment.get("provider_id"),
        "url": deployment.get("url"),
        "error": deployment.get("error"),
        "verified": deployment.get("status") == "succeeded" and bool(deployment.get("url")),
        "created_at": deployment["created_at"],
        "updated_at": deployment["updated_at"],
        "expires_at": deployment["expires_at"],
        "file_count": manifest.get("file_count", 0),
        "total_bytes": manifest.get("total_bytes", 0),
    }


async def execute_deployment(deployment_id: str) -> None:
    deployment = db.get_deployment_internal(deployment_id)
    if not deployment or deployment["status"] != "deploying":
        return
    try:
        manifest = json.loads(deployment["manifest_json"])
        workspace = settings.data_dir / "workspaces" / deployment["task_id"]
        adapter = get_adapter(deployment["target"])
        if not adapter:
            raise ValueError(f"No deployment adapter is installed for {deployment['target']}")
        result = await adapter["deploy"](workspace, manifest)
        verified = result.get("ok") is True and result.get("verified") is True
        status = "succeeded" if verified else "failed"
        db.update_deployment(
            deployment_id,
            status=status,
            provider_id=result.get("deployment_id"),
            url=result.get("url"),
            error=result.get("error") or (None if verified else "Post-deployment verification failed"),
        )
        db.add_event(
            deployment["task_id"],
            "deployment_result",
            "Déploiement vérifié et accessible." if verified else "Le déploiement a échoué ou n’a pas été vérifié.",
            {"deployment_id": deployment_id, **result},
        )
    except Exception as exc:
        db.update_deployment(deployment_id, status="failed", error=str(exc)[:1000])
        db.add_event(
            deployment["task_id"],
            "deployment_error",
            "Erreur pendant le déploiement.",
            {"deployment_id": deployment_id, "error": str(exc)[:1000]},
        )


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    user_id = read_session_token(authorization.split(" ", 1)[1])
    user = db.get_user(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user


async def handle_persistent_job(job: dict) -> None:
    if job.get("job_type") == "task" and job.get("task_id") and job.get("user_id"):
        await run_task(job["task_id"], job["user_id"])
    elif job.get("job_type") == "deployment" and job.get("deployment_id"):
        await execute_deployment(job["deployment_id"])
    else:
        raise ValueError("Job Assane AI incomplet ou non reconnu")


@app.on_event("startup")
def startup() -> None:
    global _job_worker
    settings.validate_production()
    db.init_db()
    register_local_tools()
    register_inspection_tools()
    register_browser_tools()
    register_image_tools()
    register_media_tools()
    register_operations()
    _job_worker = PersistentWorker(handle_persistent_job)
    _job_worker.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if _job_worker:
        _job_worker.stop()


@app.post("/tasks/{task_id}/android/build")
def build_android_task(task_id: str, request: AndroidBuildRequest, user: dict = Depends(current_user)) -> dict:
    tier = tier_for_user(user["id"])
    if request.variant == "release" and not tier.allow_android_release_build:
        raise HTTPException(status_code=403, detail="Le niveau actuel n’autorise pas le build Android release")
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    project = detect_project(settings.data_dir / "workspaces" / task_id)
    if project.get("type") != "android":
        raise HTTPException(status_code=400, detail="The task workspace is not detected as an Android project")
    if request.package_format == "aab" and request.variant != "release":
        raise HTTPException(status_code=400, detail="An AAB requires the release variant")
    result = build_android_artifact(task_id, request.package_format, request.variant)
    if result.get("ok") and result.get("artifact"):
        db.add_event(task_id, "android_artifact_ready", "Artefact Android vérifié et prêt au téléchargement.", {"format": request.package_format, "artifact_id": result["artifact"]["id"]})
    return {"ok": bool(result.get("ok")), "format": request.package_format, "variant": request.variant, "result": result}


@app.post("/tasks/{task_id}/preview")
def create_task_preview(task_id: str, user: dict = Depends(current_user)) -> dict:
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        preview = create_preview(user["id"], task_id, settings.data_dir / "workspaces" / task_id)
    except (OSError, PermissionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    preview["url"] = f"{settings.public_base_url.rstrip('/')}/preview/{preview['token']}/"
    db.add_event(task_id, "preview_ready", "Aperçu temporaire prêt.", {"preview_id": preview["id"], "expires_at": preview["expires_at"]})
    return {"ok": True, "preview": {key: value for key, value in preview.items() if key != "token"}, "url": preview["url"]}


@app.delete("/previews/{preview_id}")
def revoke_task_preview(preview_id: str, user: dict = Depends(current_user)) -> dict:
    if not revoke_preview(user["id"], preview_id):
        raise HTTPException(status_code=404, detail="Preview not found or already revoked")
    return {"ok": True, "status": "revoked"}


@app.get("/preview/{token}/{path:path}")
def serve_preview(token: str, path: str = ""):
    resolved = resolve_preview(token, path)
    if not resolved:
        raise HTTPException(status_code=404, detail="Preview not found or expired")
    file_path, mime = resolved
    return FileResponse(file_path, media_type=mime)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "assane-ai-core", "mode": settings.env}


@app.post("/auth/register")
def register(request: RegisterRequest) -> dict:
    email = str(request.email).strip().lower()
    phone = request.phone.strip()
    if db.get_user_by_email(email) or db.get_user_by_phone(phone):
        raise HTTPException(status_code=409, detail="Email ou numéro déjà enregistré")
    now = datetime.now(timezone.utc)
    db.delete_expired_pending_signups(now.isoformat())
    since = (now - timedelta(hours=1)).isoformat()
    if db.count_recent_otp_requests(phone, "registration", since) >= settings.otp_max_requests_per_hour:
        raise HTTPException(status_code=429, detail="Trop de demandes OTP. Réessaie plus tard.")
    pending = db.create_pending_signup(
        request.first_name,
        request.last_name,
        email,
        phone,
        hash_password(request.password),
        (now + timedelta(minutes=15)).isoformat(),
    )
    try:
        result = create_and_send(phone, "registration", pending_id=pending["id"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Le service SMS n’est pas configuré") from exc
    return {"status": "otp_required", "pending_signup_id": pending["id"], **result}


@app.post("/auth/register/resend")
def resend_registration_otp(request: OtpResendRequest) -> dict:
    pending = db.get_pending_signup(request.pending_signup_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Inscription temporaire introuvable ou expirée")
    if datetime.fromisoformat(pending["expires_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Inscription temporaire expirée")
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=1)).isoformat()
    if db.count_recent_otp_requests(pending["phone"], "registration", since) >= settings.otp_max_requests_per_hour:
        raise HTTPException(status_code=429, detail="Trop de demandes OTP. Réessaie plus tard.")
    try:
        result = create_and_send(pending["phone"], "registration", pending_id=pending["id"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Le service SMS n’est pas configuré") from exc
    return {"status": "otp_required", "pending_signup_id": pending["id"], **result}


@app.post("/auth/register/verify")
def verify_registration(request: OtpVerifyRequest) -> dict:
    result = verify_code(request.otp_request_id, request.code, "registration")
    if not result.get("ok"):
        reasons = {"expired": "Code expiré", "too_many_attempts": "Trop de tentatives", "used_or_expired": "Code déjà utilisé ou expiré"}
        raise HTTPException(status_code=400, detail=reasons.get(result.get("reason"), "Code OTP incorrect"))
    otp_request = result["request"]
    user = db.activate_pending_signup(otp_request["pending_id"])
    if not user:
        raise HTTPException(status_code=409, detail="Inscription déjà activée")
    db.set_user_tier(user["id"], "assane_moyen")
    return {"user": public_user(user), "token": create_session_token(user["id"])}


@app.post("/auth/login")
def login(request: LoginRequest) -> dict:
    user = db.get_user_by_email(str(request.email))
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password incorrect")
    return {"user": public_user(user), "token": create_session_token(user["id"])}


@app.get("/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {"user": public_user(user)}


@app.post("/auth/logout")
def logout(authorization: str | None = Header(default=None), user: dict = Depends(current_user)) -> dict:
    token = authorization.split(" ", 1)[1] if authorization and " " in authorization else ""
    revoked = revoke_session_token(token) if token else False
    return {"ok": True, "revoked": revoked}


@app.get("/tiers")
def tiers(user: dict = Depends(current_user)) -> dict:
    current = tier_for_user(user["id"])
    return {"current": public_tier(current), "tiers": [public_tier(cfg) for cfg in list_tiers()]}


@app.get("/tier")
def current_tier(user: dict = Depends(current_user)) -> dict:
    return {"tier": public_tier(tier_for_user(user["id"]))}


@app.get("/tier/limitations")
def tier_limitations(user: dict = Depends(current_user)) -> dict:
    return {"limitations": list(UNIVERSAL_LIMITATIONS)}


@app.put("/tier")
def select_tier(request: TierSelectionRequest, user: dict = Depends(current_user)) -> dict:
    try:
        cfg = get_tier(request.tier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.set_user_tier(user["id"], cfg.id)
    return {"tier": public_tier(cfg)}


@app.get("/preferences")
def preferences(user: dict = Depends(current_user)) -> dict:
    return {"preferences": db.get_preferences(user["id"])}


@app.put("/preferences")
def update_preferences(request: PreferencesRequest, user: dict = Depends(current_user)) -> dict:
    preferences = db.update_preferences(user["id"], request.theme, request.background, request.custom_instructions)
    return {"preferences": preferences}


@app.get("/skills")
def skills(user: dict = Depends(current_user)) -> dict:
    return {"skills": load_skills()}


@app.post("/skills/select")
def skill_selection(request: TaskRequest, user: dict = Depends(current_user)) -> dict:
    return {"skills": select_skills(request.prompt)}


@app.get("/instructions")
def instructions(user: dict = Depends(current_user)) -> dict:
    from ..core.instructions import system_instructions
    return {"instructions": system_instructions()}


@app.post("/inspect/url")
def inspect_public_url(request: UrlInspectRequest, user: dict = Depends(current_user)) -> dict:
    return inspect_url(request.url)


@app.post("/browser/open")
async def open_browser(request: UrlInspectRequest, user: dict = Depends(current_user)) -> dict:
    # Un workspace navigateur dédié à chaque utilisateur évite tout partage implicite.
    return await browser_open(f"user-{user['id']}-browser", request.url, screenshot=True)


@app.post("/browser/extract-images")
async def extract_public_images(request: ImageExtractionRequest, user: dict = Depends(current_user)) -> dict:
    task_id = request.task_id
    if task_id != "general" and not db.get_task(task_id, user["id"]):
        raise HTTPException(status_code=404, detail="Task not found")
    return await extract_images(task_id, request.url, request.limit, request.save, user["id"] if request.save else None)


@app.post("/inspect/file")
def inspect_workspace_file(request: FileInspectRequest, user: dict = Depends(current_user)) -> dict:
    task = db.get_task(request.task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return inspect_file(request.task_id, request.path)


@app.post("/media/generate-image")
async def generate_image_route(request: ImageGenerationRequest, user: dict = Depends(current_user)) -> dict:
    tier = tier_for_user(user["id"])
    if not tier.image_generation_enabled:
        raise HTTPException(status_code=403, detail="La génération d’images n’est pas activée pour le niveau actuel")
    return await generate_image(request.prompt, request.provider)


@app.post("/tasks")
def create_task(request: TaskRequest, user: dict = Depends(current_user)) -> dict:
    tier = tier_for_user(user["id"])
    if db.count_active_tasks(user["id"]) >= tier.max_concurrent_tasks:
        raise HTTPException(status_code=429, detail="La limite de tâches simultanées de ce niveau est atteinte")
    task = db.create_task(user["id"], request.prompt)
    db.add_event(task["id"], "created", "Tâche reçue par Assane AI.")
    db.enqueue_job("task", user["id"], task_id=task["id"])
    return {"task": db.get_task(task["id"], user["id"])}


@app.get("/tasks")
def list_tasks(limit: int = 50, user: dict = Depends(current_user)) -> dict:
    return {"tasks": db.list_tasks_for_user(user["id"], limit=limit)}


@app.get("/tasks/{task_id}")
def get_task(task_id: str, user: dict = Depends(current_user)) -> dict:
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task, "events": db.list_events(task_id)}


@app.get("/tasks/{task_id}/events")
def get_events(task_id: str, user: dict = Depends(current_user)) -> dict:
    if not db.get_task(task_id, user["id"]):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"events": db.list_events(task_id)}


@app.post("/tasks/{task_id}/stop")
def stop_task(task_id: str, user: dict = Depends(current_user)) -> dict:
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    process_stopped = runner_manager.cancel(task_id)
    db.update_task(task_id, status="stopped", current_step="stopped")
    event = db.add_event(
        task_id,
        "stopped",
        "Assane est arrêté. Envoyez un message pour continuer.",
        {"runner_process_stopped": process_stopped},
    )
    return {"ok": True, "task": db.get_task(task_id, user["id"]), "event": event}


@app.post("/tasks/{task_id}/pause")
def pause_task(task_id: str, user: dict = Depends(current_user)) -> dict:
    return stop_task(task_id, user)


@app.post("/tasks/{task_id}/continue")
def continue_task(task_id: str, user: dict = Depends(current_user)) -> dict:
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.update_task(task_id, status="queued", current_step="resume")
    db.add_event(task_id, "resumed", "Reprise demandée. Assane reprend la tâche.")
    db.enqueue_job("task", user["id"], task_id=task_id)
    return {"ok": True, "task": db.get_task(task_id, user["id"])}


@app.post("/tasks/{task_id}/confirm")
def confirm_task(task_id: str, user: dict = Depends(current_user)) -> dict:
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.add_event(task_id, "confirmed", "Confirmation reçue. Une reprise doit être implémentée selon l’action demandée.")
    return {"ok": True, "message": "Confirmation enregistrée"}


@app.get("/tasks/{task_id}/project")
def detect_task_project(task_id: str, user: dict = Depends(current_user)) -> dict:
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        project = detect_project(settings.data_dir / "workspaces" / task_id)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"project": project}


@app.get("/tasks/{task_id}/backend-plan")
def backend_plan(task_id: str, user: dict = Depends(current_user)) -> dict:
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        return {"plan": prepare_backend_plan(settings.data_dir / "workspaces" / task_id, task.get("prompt", "assane-backend"))}
    except (OSError, PermissionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/tasks/{task_id}/deploy/request")
def request_deployment(task_id: str, request: DeploymentRequest, user: dict = Depends(current_user)) -> dict:
    tier = tier_for_user(user["id"])
    task = db.get_task(task_id, user["id"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    target = request.target.strip().lower()
    if target not in tier.deployment_targets:
        raise HTTPException(status_code=403, detail="La cible de publication n’est pas autorisée pour le niveau actuel")
    adapter = get_adapter(target)
    if not adapter:
        raise HTTPException(status_code=400, detail="No deployment adapter is installed for this target")
    try:
        requested_name = normalize_project_name(request.project_name) if target == "vercel" else request.project_name.strip()
        manifest = adapter["prepare_manifest"](settings.data_dir / "workspaces" / task_id, requested_name)
        project_name = f"{manifest.get('owner')}/{manifest.get('repository')}" if target == "github" else manifest.get("project_name", requested_name)
    except (OSError, PermissionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    deployment = db.create_deployment_request(
        user["id"],
        task_id,
        target,
        project_name,
        json.dumps(manifest, ensure_ascii=False),
        expires_at,
    )
    db.add_event(
        task_id,
        "deployment_confirmation",
        f"Une demande de publication vers {target} est prête. Confirmez exactement cette demande pour continuer.",
        {"deployment_id": deployment["id"], "target": target, "project_name": project_name, "file_count": manifest["file_count"], "total_bytes": manifest["total_bytes"], "expires_at": expires_at},
    )
    return {"ok": True, "requires_confirmation": True, "deployment": public_deployment(deployment)}


@app.get("/deployments/{deployment_id}")
def get_deployment_status(deployment_id: str, user: dict = Depends(current_user)) -> dict:
    deployment = db.get_deployment(deployment_id, user["id"])
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return {"deployment": public_deployment(deployment)}


@app.post("/deployments/{deployment_id}/confirm")
def confirm_deployment(deployment_id: str, user: dict = Depends(current_user)) -> dict:
    deployment = db.get_deployment(deployment_id, user["id"])
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    now_iso = datetime.now(timezone.utc).isoformat()
    claimed = db.claim_deployment_for_execution(deployment_id, user["id"], now_iso)
    if not claimed:
        refreshed = db.get_deployment(deployment_id, user["id"])
        if refreshed and refreshed["status"] == "awaiting_confirmation" and datetime.fromisoformat(refreshed["expires_at"]) <= datetime.now(timezone.utc):
            db.update_deployment(deployment_id, status="expired", error="Confirmation expired")
            raise HTTPException(status_code=410, detail="Deployment confirmation expired")
        raise HTTPException(status_code=409, detail="Deployment request is no longer awaiting confirmation")
    db.add_event(claimed["task_id"], "deployment_confirmed", "Confirmation reçue. Publication démarrée.", {"deployment_id": deployment_id, "target": claimed["target"]})
    db.enqueue_job("deployment", user["id"], task_id=claimed["task_id"], deployment_id=deployment_id)
    return {"ok": True, "deployment": public_deployment(claimed)}


@app.post("/deployments/{deployment_id}/cancel")
def cancel_deployment(deployment_id: str, user: dict = Depends(current_user)) -> dict:
    deployment = db.get_deployment(deployment_id, user["id"])
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    cancelled = db.cancel_pending_deployment(deployment_id, user["id"])
    if not cancelled:
        raise HTTPException(status_code=409, detail="Only a pending deployment can be cancelled")
    db.add_event(cancelled["task_id"], "deployment_cancelled", "Demande de publication annulée avant exécution.", {"deployment_id": deployment_id})
    return {"ok": True, "deployment": public_deployment(cancelled)}


@app.post("/uploads")
async def upload_file(file: UploadFile = File(...), task_id: str = "general", user: dict = Depends(current_user)) -> dict:
    if task_id != "general" and not db.get_task(task_id, user["id"]):
        raise HTTPException(status_code=404, detail="Task not found")
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large for the configured upload limit")
    try:
        artifact = save_artifact(user["id"], task_id, file.filename or "artifact.bin", content, file.content_type or "application/octet-stream")
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return {"ok": True, "artifact": artifact}


@app.get("/artifacts/{artifact_id}/download")
def download_artifact(artifact_id: str, user: dict = Depends(current_user)):
    artifact = get_artifact(user["id"], artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    path = artifact["path"]
    if not Path(path).is_file():
        raise HTTPException(status_code=404, detail="Artifact file missing")
    return FileResponse(path, media_type=artifact["mime_type"], filename=artifact["filename"])


@app.get("/providers/status")
def provider_status(user: dict = Depends(current_user)) -> dict:
    return {
        "ok": True,
        "capabilities": {
            "assistant": bool(settings.manus_api_key or settings.mistral_api_key or settings.openai_api_key),
            "image_generation": bool(settings.openai_api_key or settings.stability_api_key),
            "deployment": bool(settings.vercel_token or settings.github_token or settings.cloudflare_token),
            "source_control": bool(settings.github_token),
            "speech": bool(settings.deepgram_api_key or settings.openai_api_key),
        },
    }


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
        "phone": user["phone"],
        "phone_verified": bool(user.get("phone_verified", False)),
    }
