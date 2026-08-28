from __future__ import annotations

import asyncio
import logging

from app.api.main import execute_deployment, handle_persistent_job
from app.core.config import settings
from app.jobs.worker import PersistentWorker
from app.storage import db

logging.basicConfig(level=logging.INFO)


def main() -> None:
    settings.validate_production()
    db.init_db()
    worker = PersistentWorker(handle_persistent_job)
    worker.start()
    try:
        while True:
            asyncio.run(asyncio.sleep(60))
    except KeyboardInterrupt:
        worker.stop()


if __name__ == "__main__":
    main()
