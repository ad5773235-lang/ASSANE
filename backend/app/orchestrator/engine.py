from __future__ import annotations

import asyncio
import json
from typing import Any

from ..core.config import settings
from ..core.instructions import system_instructions
from ..core.providers import manus_create_task, mistral_chat, openai_chat, ProviderError
from ..skills.loader import select_skills
from ..storage import db
from ..tiers.config import get_tier
from ..tools.inspect_tools import inspect_file, inspect_url
from ..tools.browser_tools import browser_open
from ..tools.local_tools import build_apk, list_files, read_file, run_android_tests, run_command, write_file
from ..tools.media_tools import generate_image
from ..tools.operations import deploy, download_artifact, save_workspace, share_artifact


FINAL_STATES = {"succeeded", "failed", "cancelled"}


async def ask_model(prompt: str, context: list[dict[str, str]], custom_instructions: str = "") -> dict[str, Any]:
    system = (
        system_instructions()
        + "\n\nTu es le moteur de décision d'Assane AI. Réponds en JSON avec kind parmi "
        "tool_call, final ou confirmation. Pour tool_call, fournis tool et arguments. "
        "Ne prétends jamais qu'une action a réussi sans observation réelle. "
        "Pour publier, supprimer, partager ou déployer, retourne confirmation avant l'action."
    )
    if custom_instructions.strip():
        system += "\n\nINSTRUCTIONS PERSONNALISÉES DE CET UTILISATEUR :\n" + custom_instructions.strip()
    messages = [{"role": "system", "content": system}, *context, {"role": "user", "content": prompt}]
    if settings.manus_api_key:
        return {"provider": "manus", "result": await manus_create_task(prompt)}
    if settings.mistral_api_key:
        return {"provider": "mistral", "result": await mistral_chat(messages)}
    if settings.openai_api_key:
        return {"provider": "openai", "result": await openai_chat(messages)}
    raise ProviderError("Aucun modèle configuré : renseignez MANUS_API_KEY, MISTRAL_API_KEY ou OPENAI_API_KEY")


def normalize_decision(raw: dict[str, Any]) -> dict[str, Any]:
    result = raw.get("result", raw)
    if raw.get("provider") == "manus":
        return {"kind": "external_task", "provider": "manus", "result": result}
    choices = result.get("choices", []) if isinstance(result, dict) else []
    content = choices[0].get("message", {}).get("content", "") if choices else ""
    if isinstance(content, dict):
        return content
    import json
    try:
        return json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return {"kind": "final", "message": str(content)}


async def dispatch_tool(task_id: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    handlers = {
        "list_files": list_files,
        "read_file": read_file,
        "write_file": write_file,
        "run_command": run_command,
        "inspect_file": inspect_file,
        "inspect_url": inspect_url,
        "browser_open": browser_open,
    }
    if tool == "build_apk":
        return build_apk(task_id, **arguments)
    if tool == "run_android_tests":
        return run_android_tests(task_id)
    if tool == "generate_image":
        return await generate_image(**arguments)
    if tool == "save_workspace":
        return save_workspace(task_id)
    if tool == "download_artifact":
        return download_artifact(**arguments)
    if tool == "share_artifact":
        return share_artifact(**arguments)
    if tool == "deploy":
        return deploy(task_id, **arguments)
    if tool not in handlers:
        return {"ok": False, "error": "tool_not_available", "tool": tool}
    return handlers[tool](task_id, **arguments)


def task_control_state(task_id: str, user_id: str) -> str | None:
    task = db.get_task(task_id, user_id)
    return task.get("status") if task else None


async def run_task(task_id: str, user_id: str) -> None:
    task = db.get_task(task_id, user_id)
    if not task:
        return
    initial = task_control_state(task_id, user_id)
    if initial in {"paused", "stopped", "cancelled"}:
        return
    try:
        tier = get_tier(db.get_user_tier(user_id))
    except ValueError:
        tier = get_tier("assane_moyen")
    db.update_task(task_id, status="planning", current_step="skills")
    db.add_event(task_id, "status", "Assane analyse la demande et sélectionne les Skills.")
    skills = select_skills(task["prompt"])
    db.add_event(task_id, "skills", "Skills sélectionnés.", {"skills": [s["id"] for s in skills]})
    db.update_task(task_id, status="running", current_step="decision")

    context: list[dict[str, str]] = []
    preferences = db.get_preferences(user_id)
    for iteration in range(min(settings.max_iterations, tier.max_iterations)):
        current_status = task_control_state(task_id, user_id)
        if current_status in {"paused", "stopped", "cancelled"}:
            db.add_event(task_id, "stopped", "Assane est arrêté. Envoyez un message pour continuer.")
            return
        db.update_task(task_id, iteration=iteration + 1, current_step="decision")
        db.add_event(task_id, "thinking", "Assane réfléchit à la prochaine action.", {"iteration": iteration + 1})
        try:
            raw = await ask_model(task["prompt"], context, preferences.get("custom_instructions", ""))
            decision = normalize_decision(raw)
        except ProviderError as exc:
            message = str(exc)
            lost = "timeout" in message.lower() or "connect" in message.lower() or "network" in message.lower()
            kind = "connection_lost" if lost else "error"
            text = "Connexion perdue. Vérifiez le réseau puis envoyez un message pour continuer." if lost else "Le fournisseur IA a renvoyé une erreur."
            db.add_event(task_id, kind, text, {"error": message})
            db.update_task(task_id, status="connection_lost" if lost else "failed", current_step="connection_lost" if lost else "provider_error")
            return
        except Exception as exc:
            db.add_event(task_id, "error", "Le fournisseur IA a renvoyé une erreur.", {"error": str(exc)})
            db.update_task(task_id, status="failed", current_step="provider_error")
            return

        if decision.get("kind") == "external_task":
            db.add_event(task_id, "provider", "Tâche envoyée à Manus via son API.", {"response": decision.get("result")})
            db.update_task(task_id, status="succeeded", current_step="completed")
            return

        if decision.get("kind") == "confirmation":
            db.add_event(task_id, "confirmation", decision.get("message", "Confirmation requise."), decision)
            db.update_task(task_id, status="awaiting_confirmation", current_step="confirmation")
            return

        if decision.get("kind") == "final":
            db.add_event(task_id, "final", decision.get("message", "Tâche terminée."), decision)
            db.update_task(task_id, status="succeeded", current_step="completed")
            return

        if decision.get("kind") != "tool_call":
            db.add_event(task_id, "error", "Décision du modèle invalide.", decision)
            db.update_task(task_id, status="failed", current_step="invalid_decision")
            return

        tool = decision.get("tool", "")
        arguments = decision.get("arguments", {})
        db.add_event(task_id, "tool_start", f"Exécution de {tool}.", {"arguments": arguments})
        result = await dispatch_tool(task_id, tool, arguments)
        db.add_event(task_id, "tool_result", f"Résultat de {tool}.", result)
        db.update_task(task_id, checkpoint_json=json.dumps({"iteration": iteration + 1, "tool": tool, "arguments": arguments, "result": result}, ensure_ascii=False, default=str))
        if task_control_state(task_id, user_id) in {"paused", "stopped", "cancelled"}:
            db.add_event(task_id, "stopped", "Assane est arrêté. Envoyez un message pour continuer.")
            return
        context.append({"role": "assistant", "content": str(decision)})
        context.append({"role": "tool", "content": str(result)})
        if not result.get("ok", False):
            context.append({"role": "system", "content": "L'outil a échoué. Analyse l'erreur avant de réessayer."})
        await asyncio.sleep(0)

    db.add_event(task_id, "error", "Limite d’itérations atteinte.")
    db.update_task(task_id, status="failed", current_step="iteration_limit")
