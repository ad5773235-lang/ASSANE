from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..core.config import settings

DB_PATH = settings.data_dir / "assane.db"


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT NOT NULL, password_hash TEXT NOT NULL, phone_verified BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), token_hash TEXT UNIQUE NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMPTZ NOT NULL, revoked_at TIMESTAMPTZ);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, expires_at);
CREATE TABLE IF NOT EXISTS account_tiers (user_id TEXT PRIMARY KEY REFERENCES users(id), tier_id TEXT NOT NULL DEFAULT 'assane_moyen', updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_account_tiers_tier ON account_tiers(tier_id);
CREATE TABLE IF NOT EXISTS user_preferences (user_id TEXT PRIMARY KEY REFERENCES users(id), theme TEXT NOT NULL DEFAULT 'dark', background TEXT NOT NULL DEFAULT 'default', custom_instructions TEXT NOT NULL DEFAULT '', updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), prompt TEXT NOT NULL, status TEXT NOT NULL, current_step TEXT NOT NULL, iteration INTEGER NOT NULL DEFAULT 0, checkpoint_json TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS events (id BIGSERIAL PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), kind TEXT NOT NULL, message TEXT NOT NULL, data_json TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS artifacts (id TEXT PRIMARY KEY, task_id TEXT NOT NULL, user_id TEXT NOT NULL REFERENCES users(id), filename TEXT NOT NULL, path TEXT NOT NULL, mime_type TEXT NOT NULL, sha256 TEXT NOT NULL, size_bytes BIGINT NOT NULL DEFAULT 0, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS preview_links (id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL, user_id TEXT NOT NULL REFERENCES users(id), task_id TEXT NOT NULL REFERENCES tasks(id), root_path TEXT NOT NULL, entry_path TEXT NOT NULL DEFAULT 'index.html', status TEXT NOT NULL DEFAULT 'active', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMPTZ NOT NULL);
CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, job_type TEXT NOT NULL, task_id TEXT, deployment_id TEXT, user_id TEXT NOT NULL REFERENCES users(id), status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0, available_at TIMESTAMPTZ NOT NULL, locked_at TIMESTAMPTZ, last_error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_jobs_claim ON jobs(status, available_at, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_task ON jobs(task_id, job_type, status);
CREATE TABLE IF NOT EXISTS pending_signups (id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT NOT NULL, password_hash TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_pending_signups_phone ON pending_signups(phone, expires_at);
CREATE TABLE IF NOT EXISTS otp_requests (id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id), pending_id TEXT REFERENCES pending_signups(id), phone_number TEXT NOT NULL, code_hash TEXT NOT NULL, purpose TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, verified_at TIMESTAMPTZ);
CREATE INDEX IF NOT EXISTS idx_otp_phone_purpose ON otp_requests(phone_number, purpose, status, created_at);
CREATE TABLE IF NOT EXISTS deployment_requests (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), task_id TEXT NOT NULL REFERENCES tasks(id), target TEXT NOT NULL, project_name TEXT NOT NULL, manifest_json TEXT NOT NULL, status TEXT NOT NULL, provider_id TEXT, url TEXT, error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMPTZ NOT NULL);
"""


class _PostgresConnection:
    def __init__(self, raw: Any) -> None:
        self.raw = raw

    def __enter__(self) -> "_PostgresConnection":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if exc_type:
            self.raw.rollback()
        else:
            self.raw.commit()
        self.raw.close()

    def execute(self, query: str, params: Any = ()) -> Any:
        return self.raw.execute(query.replace("?", "%s"), params)

    def commit(self) -> None:
        self.raw.commit()

    def executescript(self, script: str) -> None:
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)


def using_postgres() -> bool:
    return settings.database_url.startswith(("postgres://", "postgresql://"))


def connect() -> Any:
    if using_postgres():
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgreSQL configuré mais psycopg[binary] n’est pas installé") from exc
        return _PostgresConnection(psycopg.connect(settings.database_url, row_factory=dict_row))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        if using_postgres():
            conn.executescript(POSTGRES_SCHEMA)
            return
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                phone_verified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                token_hash TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                revoked_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, expires_at);
            CREATE TABLE IF NOT EXISTS account_tiers (
                user_id TEXT PRIMARY KEY REFERENCES users(id),
                tier_id TEXT NOT NULL DEFAULT 'assane_moyen',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_account_tiers_tier ON account_tiers(tier_id);
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY REFERENCES users(id),
                theme TEXT NOT NULL DEFAULT 'dark',
                background TEXT NOT NULL DEFAULT 'default',
                custom_instructions TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                prompt TEXT NOT NULL,
                status TEXT NOT NULL,
                current_step TEXT NOT NULL,
                iteration INTEGER NOT NULL DEFAULT 0,
                checkpoint_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL REFERENCES tasks(id),
                kind TEXT NOT NULL,
                message TEXT NOT NULL,
                data_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                user_id TEXT NOT NULL REFERENCES users(id),
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS preview_links (
                id TEXT PRIMARY KEY,
                token_hash TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL REFERENCES users(id),
                task_id TEXT NOT NULL REFERENCES tasks(id),
                root_path TEXT NOT NULL,
                entry_path TEXT NOT NULL DEFAULT 'index.html',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                task_id TEXT,
                deployment_id TEXT,
                user_id TEXT NOT NULL REFERENCES users(id),
                status TEXT NOT NULL DEFAULT 'queued',
                attempts INTEGER NOT NULL DEFAULT 0,
                available_at TEXT NOT NULL,
                locked_at TEXT,
                last_error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_claim ON jobs(status, available_at, created_at);
            CREATE INDEX IF NOT EXISTS idx_jobs_task ON jobs(task_id, job_type, status);
            CREATE TABLE IF NOT EXISTS pending_signups (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pending_signups_phone ON pending_signups(phone, expires_at);
            CREATE TABLE IF NOT EXISTS otp_requests (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                pending_id TEXT REFERENCES pending_signups(id),
                phone_number TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                purpose TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                verified_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_otp_phone_purpose ON otp_requests(phone_number, purpose, status, created_at);
            CREATE TABLE IF NOT EXISTS deployment_requests (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                task_id TEXT NOT NULL REFERENCES tasks(id),
                target TEXT NOT NULL,
                project_name TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                status TEXT NOT NULL,
                provider_id TEXT,
                url TEXT,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL
            );
            """
        )
        # Les artefacts "general" sont valides avant toute création de tâche.
        # Les anciennes bases avaient une FK vers tasks qui rendait ces uploads impossibles.
        foreign_key = conn.execute("PRAGMA foreign_key_list(artifacts)").fetchall()
        if any(row["table"] == "tasks" for row in foreign_key):
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("CREATE TABLE artifacts_migrated (id TEXT PRIMARY KEY, task_id TEXT NOT NULL, user_id TEXT NOT NULL REFERENCES users(id), filename TEXT NOT NULL, path TEXT NOT NULL, mime_type TEXT NOT NULL, sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()}
            size_expression = "size_bytes" if "size_bytes" in columns else "0"
            conn.execute(f"INSERT INTO artifacts_migrated(id, task_id, user_id, filename, path, mime_type, sha256, size_bytes, created_at) SELECT id, task_id, user_id, filename, path, mime_type, sha256, {size_expression}, created_at FROM artifacts")
            conn.execute("DROP TABLE artifacts")
            conn.execute("ALTER TABLE artifacts_migrated RENAME TO artifacts")
            conn.execute("PRAGMA foreign_keys = ON")
        for statement in (
            "ALTER TABLE tasks ADD COLUMN checkpoint_json TEXT",
            "ALTER TABLE artifacts ADD COLUMN size_bytes INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN phone_verified INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
        ):
            try:
                conn.execute(statement)
            except sqlite3.OperationalError:
                pass


def user_storage_bytes(user_id: str) -> int:
    with connect() as conn:
        row = conn.execute("SELECT COALESCE(SUM(size_bytes), 0) AS total FROM artifacts WHERE user_id = ?", (user_id,)).fetchone()
    return int(row["total"]) if row else 0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def recover_running_jobs() -> int:
    """Remet en file les jobs interrompus par l’arrêt du processus backend."""
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE jobs SET status = 'queued', locked_at = NULL, updated_at = CURRENT_TIMESTAMP "
            "WHERE status = 'running'"
        )
    return cursor.rowcount


def enqueue_job(job_type: str, user_id: str, task_id: str | None = None, deployment_id: str | None = None) -> dict[str, Any]:
    """Insère un job idempotent; un même travail ne peut pas avoir deux jobs actifs."""
    now = utc_now()
    with connect() as conn:
        where = "job_type = ? AND user_id = ? AND status IN ('queued', 'running')"
        values: list[Any] = [job_type, user_id]
        if task_id is not None:
            where += " AND task_id = ?"
            values.append(task_id)
        if deployment_id is not None:
            where += " AND deployment_id = ?"
            values.append(deployment_id)
        existing = conn.execute(f"SELECT * FROM jobs WHERE {where} ORDER BY created_at DESC LIMIT 1", values).fetchone()
        if existing:
            return dict(existing)
        job_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO jobs(id, job_type, task_id, deployment_id, user_id, status, available_at) VALUES (?, ?, ?, ?, ?, 'queued', ?)",
            (job_id, job_type, task_id, deployment_id, user_id, now),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else {}


def claim_next_job() -> dict[str, Any] | None:
    """Réserve un job avec BEGIN IMMEDIATE pour éviter deux workers concurrents."""
    now = utc_now()
    with connect() as conn:
        conn.execute("BEGIN" if using_postgres() else "BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM jobs WHERE status = 'queued' AND available_at <= ? ORDER BY created_at LIMIT 1",
            (now,),
        ).fetchone()
        if not row:
            conn.commit()
            return None
        job_id = row["id"]
        conn.execute(
            "UPDATE jobs SET status = 'running', attempts = attempts + 1, locked_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'queued'",
            (now, job_id),
        )
        claimed = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(claimed) if claimed else None


def finish_job(job_id: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'succeeded', locked_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (job_id,),
        )


def fail_job(job_id: str, error: str, max_attempts: int = 3) -> None:
    with connect() as conn:
        row = conn.execute("SELECT attempts FROM jobs WHERE id = ?", (job_id,)).fetchone()
        attempts = int(row["attempts"]) if row else max_attempts
        if attempts < max_attempts:
            delay_seconds = min(60, 2 ** attempts)
            available = datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + delay_seconds, timezone.utc).isoformat()
            conn.execute(
                "UPDATE jobs SET status = 'queued', available_at = ?, locked_at = NULL, last_error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (available, error[:1000], job_id),
            )
        else:
            conn.execute(
                "UPDATE jobs SET status = 'failed', locked_at = NULL, last_error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (error[:1000], job_id),
            )


def get_job(job_id: str, user_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ? AND user_id = ?", (job_id, user_id)).fetchone()
    return dict(row) if row else None


def create_user(first_name: str, last_name: str, email: str, phone: str, password_hash: str) -> dict[str, Any]:
    user_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT INTO users(id, first_name, last_name, email, phone, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, first_name.strip(), last_name.strip(), email.strip().lower(), phone.strip(), password_hash),
        )
    return get_user(user_id)


def create_session(session_id: str, user_id: str, token_hash: str, expires_at: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions(id, user_id, token_hash, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, token_hash, expires_at),
        )


def session_is_active(session_id: str, user_id: str, token_hash: str, now_iso: str) -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE id = ? AND user_id = ? AND token_hash = ? AND revoked_at IS NULL AND expires_at > ?",
            (session_id, user_id, token_hash, now_iso),
        ).fetchone()
    return row is not None


def revoke_session(token_hash: str) -> bool:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE sessions SET revoked_at = CURRENT_TIMESTAMP WHERE token_hash = ? AND revoked_at IS NULL",
            (token_hash,),
        )
    return cursor.rowcount == 1


def get_user(user_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    return dict(row) if row else None


def set_user_tier(user_id: str, tier_id: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO account_tiers(user_id, tier_id) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET tier_id=excluded.tier_id, updated_at=CURRENT_TIMESTAMP",
            (user_id, tier_id),
        )


def get_user_tier(user_id: str, default: str = "assane_moyen") -> str:
    with connect() as conn:
        row = conn.execute("SELECT tier_id FROM account_tiers WHERE user_id = ?", (user_id,)).fetchone()
    return str(row["tier_id"]) if row else default


def count_active_tasks(user_id: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ? AND status IN ('queued', 'planning', 'running')",
            (user_id,),
        ).fetchone()
    return int(row["count"]) if row else 0


def get_preferences(user_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            conn.execute("INSERT INTO user_preferences(user_id) VALUES (?)", (user_id,))
            row = conn.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row)


def update_preferences(user_id: str, theme: str, background: str, custom_instructions: str) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            "INSERT INTO user_preferences(user_id, theme, background, custom_instructions) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET theme=excluded.theme, background=excluded.background, "
            "custom_instructions=excluded.custom_instructions, updated_at=CURRENT_TIMESTAMP",
            (user_id, theme, background, custom_instructions),
        )
    return get_preferences(user_id)


def create_task(user_id: str, prompt: str) -> dict[str, Any]:
    task_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT INTO tasks(id, user_id, prompt, status, current_step) VALUES (?, ?, ?, 'queued', 'planning')",
            (task_id, user_id, prompt),
        )
    return get_task(task_id, user_id)


def get_task(task_id: str, user_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)).fetchone()
    return dict(row) if row else None


def list_tasks_for_user(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Retourne uniquement les tâches du compte, avec un résumé d’événements réel."""
    safe_limit = max(1, min(int(limit), 100))
    with connect() as conn:
        rows = conn.execute(
            "SELECT t.*, "
            "(SELECT COUNT(*) FROM events e WHERE e.task_id = t.id) AS event_count, "
            "(SELECT e.message FROM events e WHERE e.task_id = t.id ORDER BY e.id DESC LIMIT 1) AS last_event_message "
            "FROM tasks t WHERE t.user_id = ? ORDER BY t.updated_at DESC, t.created_at DESC LIMIT ?",
            (user_id, safe_limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_task_internal(task_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def update_task(task_id: str, **fields: Any) -> None:
    allowed = {"status", "current_step", "iteration", "checkpoint_json"}
    clean = {key: value for key, value in fields.items() if key in allowed}
    if not clean:
        return
    assignments = ", ".join(f"{key} = ?" for key in clean)
    values = list(clean.values()) + [task_id]
    with connect() as conn:
        conn.execute(f"UPDATE tasks SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)


def create_preview_link(link_id: str, token_hash: str, user_id: str, task_id: str, root_path: str, entry_path: str, expires_at: str) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            "INSERT INTO preview_links(id, token_hash, user_id, task_id, root_path, entry_path, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (link_id, token_hash, user_id, task_id, root_path, entry_path, expires_at),
        )
    return get_preview_link_by_token(token_hash) or {}


def get_preview_link_by_token(token_hash: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM preview_links WHERE token_hash = ?", (token_hash,)).fetchone()
    return dict(row) if row else None


def revoke_preview_link(link_id: str, user_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE preview_links SET status = 'revoked' WHERE id = ? AND user_id = ? AND status = 'active'",
            (link_id, user_id),
        )
    return cursor.rowcount == 1


def create_deployment_request(user_id: str, task_id: str, target: str, project_name: str, manifest_json: str, expires_at: str) -> dict[str, Any]:
    deployment_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT INTO deployment_requests(id, user_id, task_id, target, project_name, manifest_json, status, expires_at) VALUES (?, ?, ?, ?, ?, ?, 'awaiting_confirmation', ?)",
            (deployment_id, user_id, task_id, target, project_name, manifest_json, expires_at),
        )
    return get_deployment(deployment_id, user_id) or {}


def get_deployment(deployment_id: str, user_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM deployment_requests WHERE id = ? AND user_id = ?",
            (deployment_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def get_deployment_internal(deployment_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM deployment_requests WHERE id = ?", (deployment_id,)).fetchone()
    return dict(row) if row else None


def get_pending_deployment(task_id: str, user_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM deployment_requests WHERE task_id = ? AND user_id = ? AND status = 'awaiting_confirmation' ORDER BY created_at DESC LIMIT 1",
            (task_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def cancel_pending_deployment(deployment_id: str, user_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE deployment_requests SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND user_id = ? AND status = 'awaiting_confirmation'",
            (deployment_id, user_id),
        )
        if cursor.rowcount != 1:
            return None
        row = conn.execute(
            "SELECT * FROM deployment_requests WHERE id = ? AND user_id = ?",
            (deployment_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def claim_deployment_for_execution(deployment_id: str, user_id: str, now_iso: str) -> dict[str, Any] | None:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE deployment_requests SET status = 'deploying', updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND user_id = ? AND status = 'awaiting_confirmation' AND expires_at > ?",
            (deployment_id, user_id, now_iso),
        )
        if cursor.rowcount != 1:
            return None
        row = conn.execute(
            "SELECT * FROM deployment_requests WHERE id = ? AND user_id = ?",
            (deployment_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def update_deployment(deployment_id: str, **fields: Any) -> None:
    allowed = {"status", "provider_id", "url", "error"}
    clean = {key: value for key, value in fields.items() if key in allowed}
    if not clean:
        return
    assignments = ", ".join(f"{key} = ?" for key in clean)
    values = list(clean.values()) + [deployment_id]
    with connect() as conn:
        conn.execute(
            f"UPDATE deployment_requests SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )


def add_event(task_id: str, kind: str, message: str, data: Any | None = None) -> dict[str, Any]:
    with connect() as conn:
        if using_postgres():
            cursor = conn.execute(
                "INSERT INTO events(task_id, kind, message, data_json) VALUES (?, ?, ?, ?) RETURNING id",
                (task_id, kind, message, json.dumps(data, ensure_ascii=False) if data is not None else None),
            )
            returned = cursor.fetchone()
            event_id = returned["id"] if returned else None
        else:
            cursor = conn.execute(
                "INSERT INTO events(task_id, kind, message, data_json) VALUES (?, ?, ?, ?)",
                (task_id, kind, message, json.dumps(data, ensure_ascii=False) if data is not None else None),
            )
            event_id = cursor.lastrowid
    return {"id": event_id, "task_id": task_id, "kind": kind, "message": message, "data": data}


def list_events(task_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM events WHERE task_id = ? ORDER BY id", (task_id,)).fetchall()
    return [
        {**dict(row), "data": json.loads(row["data_json"]) if row["data_json"] else None}
        for row in rows
    ]


# --- OTP et inscriptions temporaires -------------------------------------------------

def create_pending_signup(first_name: str, last_name: str, email: str, phone: str, password_hash: str, expires_at: str) -> dict[str, Any]:
    pending_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT INTO pending_signups(id, first_name, last_name, email, phone, password_hash, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pending_id, first_name.strip(), last_name.strip(), email.strip().lower(), phone.strip(), password_hash, expires_at),
        )
        row = conn.execute("SELECT * FROM pending_signups WHERE id = ?", (pending_id,)).fetchone()
    return dict(row) if row else {}


def get_pending_signup(pending_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM pending_signups WHERE id = ?", (pending_id,)).fetchone()
    return dict(row) if row else None


def count_recent_otp_requests(phone_number: str, purpose: str, since_iso: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM otp_requests WHERE phone_number = ? AND purpose = ? AND created_at >= ?",
            (phone_number, purpose, since_iso),
        ).fetchone()
    return int(row["count"]) if row else 0


def invalidate_active_otps(phone_number: str, purpose: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE otp_requests SET status = 'superseded' WHERE phone_number = ? AND purpose = ? AND status = 'pending'",
            (phone_number, purpose),
        )


def create_otp_request(request_id: str, user_id: str | None, pending_id: str | None, phone_number: str, code_hash: str, purpose: str, expires_at: str, max_attempts: int) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO otp_requests(id, user_id, pending_id, phone_number, code_hash, purpose, expires_at, max_attempts) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (request_id, user_id, pending_id, phone_number, code_hash, purpose, expires_at, max_attempts),
        )


def get_otp_request(request_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM otp_requests WHERE id = ?", (request_id,)).fetchone()
    return dict(row) if row else None


def increment_otp_attempt(request_id: str) -> int:
    with connect() as conn:
        conn.execute("UPDATE otp_requests SET attempt_count = attempt_count + 1 WHERE id = ? AND status = 'pending'", (request_id,))
        row = conn.execute("SELECT attempt_count FROM otp_requests WHERE id = ?", (request_id,)).fetchone()
    return int(row["attempt_count"]) if row else 0


def expire_otp(request_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE otp_requests SET status = 'expired' WHERE id = ? AND status = 'pending'", (request_id,))


def fail_otp(request_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE otp_requests SET status = 'failed' WHERE id = ? AND status = 'pending'", (request_id,))


def verify_otp(request_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE otp_requests SET status = 'verified', verified_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'pending'", (request_id,))


def activate_pending_signup(pending_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        pending = conn.execute("SELECT * FROM pending_signups WHERE id = ?", (pending_id,)).fetchone()
        if not pending:
            return None
        user_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users(id, first_name, last_name, email, phone, password_hash, phone_verified) VALUES (?, ?, ?, ?, ?, ?, 1)",
            (user_id, pending["first_name"], pending["last_name"], pending["email"], pending["phone"], pending["password_hash"]),
        )
        conn.execute("UPDATE otp_requests SET pending_id = NULL WHERE pending_id = ?", (pending_id,))
        conn.execute("DELETE FROM pending_signups WHERE id = ?", (pending_id,))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def phone_is_verified(user_id: str) -> bool:
    with connect() as conn:
        row = conn.execute("SELECT phone_verified FROM users WHERE id = ?", (user_id,)).fetchone()
    return bool(row and row["phone_verified"])


def get_user_by_phone(phone: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE phone = ?", (phone.strip(),)).fetchone()
    return dict(row) if row else None


def delete_expired_pending_signups(now_iso: str) -> int:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM pending_signups WHERE expires_at <= ?", (now_iso,))
    return cursor.rowcount
