from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Awaitable, Callable
from typing import Any

from ..storage import db

logger = logging.getLogger(__name__)
JobHandler = Callable[[dict[str, Any]], Awaitable[None]]


class PersistentWorker:
    """Worker intégré au backend; la file et les états restent en base SQLite.

    Ce n'est pas encore un système distribué : une instance de worker par processus
    est attendue. Le verrouillage de la base évite toutefois les doubles claims.
    """

    def __init__(self, handler: JobHandler, poll_seconds: float = 0.75) -> None:
        self.handler = handler
        self.poll_seconds = poll_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        db.recover_running_jobs()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="assane-job-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop.is_set():
            job = db.claim_next_job()
            if not job:
                self._stop.wait(self.poll_seconds)
                continue
            try:
                asyncio.run(self.handler(job))
            except Exception as exc:  # pragma: no cover - dernier filet du worker
                logger.exception("Assane job %s failed", job.get("id"))
                db.fail_job(job["id"], str(exc))
            else:
                db.finish_job(job["id"])


__all__ = ["PersistentWorker"]


if __name__ == "__main__":
    raise SystemExit("Le worker est lancé par le processus backend, pas directement.")
