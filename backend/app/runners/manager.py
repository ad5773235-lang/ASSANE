from __future__ import annotations

import os
import signal
import subprocess
import threading
from pathlib import Path
from typing import Any

from ..core.config import settings
from ..tools.local_tools import workspace_for


class RunnerManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._processes: dict[str, subprocess.Popen[str]] = {}
        self._docker_names: dict[str, str] = {}

    def execute(self, task_id: str, program: str, args: list[str], timeout_seconds: int) -> dict[str, Any]:
        if settings.runner_mode == "docker":
            return self._docker(task_id, program, args, timeout_seconds)
        return self._local(task_id, program, args, timeout_seconds)

    def cancel(self, task_id: str) -> bool:
        """Arrête le processus de la tâche; retourne False si aucun processus n'est actif."""
        with self._lock:
            process = self._processes.get(task_id)
            docker_name = self._docker_names.get(task_id)
        if process and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            return True
        if docker_name:
            subprocess.run(["docker", "rm", "-f", docker_name], capture_output=True, text=True, timeout=10)
            return True
        return False

    def _register(self, task_id: str, process: subprocess.Popen[str], docker_name: str | None = None) -> None:
        with self._lock:
            self._processes[task_id] = process
            if docker_name:
                self._docker_names[task_id] = docker_name

    def _unregister(self, task_id: str) -> None:
        with self._lock:
            self._processes.pop(task_id, None)
            self._docker_names.pop(task_id, None)

    def _local(self, task_id: str, program: str, args: list[str], timeout_seconds: int) -> dict[str, Any]:
        workspace = workspace_for(task_id)
        process: subprocess.Popen[str] | None = None
        try:
            process = subprocess.Popen(
                [program, *args],
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
                env={"PATH": os.getenv("PATH", ""), "HOME": str(workspace), "LANG": "C.UTF-8"},
            )
            self._register(task_id, process)
            stdout, stderr = process.communicate(timeout=min(timeout_seconds, settings.task_timeout_seconds))
            return {
                "ok": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout[-20_000:],
                "stderr": stderr[-20_000:],
                "runner": "local-development",
            }
        except subprocess.TimeoutExpired:
            if process:
                self.cancel(task_id)
            return {"ok": False, "error": "timeout", "runner": "local-development"}
        except FileNotFoundError:
            return {"ok": False, "error": "program_not_available", "runner": "local-development"}
        finally:
            self._unregister(task_id)

    def _docker(self, task_id: str, program: str, args: list[str], timeout_seconds: int) -> dict[str, Any]:
        workspace = workspace_for(task_id).resolve()
        docker_name = "assane-" + task_id.replace("-", "")[:24]
        command = [
            "docker", "run", "--rm", "--name", docker_name,
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--pids-limit", "256",
            "--memory", "4g",
            "--cpus", "2",
            "--user", "1000:1000",
            "-v", f"{workspace}:/workspace:rw",
            "-w", "/workspace",
            settings.docker_image,
            program,
            *args,
        ]
        process: subprocess.Popen[str] | None = None
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            self._register(task_id, process, docker_name)
            stdout, stderr = process.communicate(timeout=min(timeout_seconds, settings.task_timeout_seconds))
            return {
                "ok": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout[-20_000:],
                "stderr": stderr[-20_000:],
                "runner": "docker-hardened",
            }
        except FileNotFoundError:
            return {"ok": False, "error": "docker_not_available", "runner": "docker-hardened"}
        except subprocess.TimeoutExpired:
            if process:
                self.cancel(task_id)
            return {"ok": False, "error": "timeout", "runner": "docker-hardened"}
        finally:
            self._unregister(task_id)


runner_manager = RunnerManager()
