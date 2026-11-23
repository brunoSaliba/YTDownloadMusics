"""Runs the yt-dlp worker in a killable child process with bounded concurrency."""

import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("app.jobs")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKDIR_PREFIX = "ytdl-"
STALE_WORKDIR_SECONDS = 600


@dataclass
class WorkerResult:
    ok: bool
    error: str | None = None
    info: dict | None = None


class Slots:
    """Non-blocking concurrency limiter: acquire() returns False when full."""

    def __init__(self, size: int):
        self._sem = threading.BoundedSemaphore(size)

    def acquire(self) -> bool:
        return self._sem.acquire(blocking=False)

    def release(self) -> None:
        self._sem.release()


def worker_command(*args: str) -> list[str]:
    return [sys.executable, "-m", "app.worker", *args]


def _kill(proc: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (ProcessLookupError, PermissionError, OSError):
        pass


def run_worker(args: list[str], timeout: int) -> WorkerResult:
    """Run the worker with fixed argv (no shell); kill its process group on timeout."""
    kwargs = {"start_new_session": True} if os.name == "posix" else {}
    proc = subprocess.Popen(  # noqa: S603 - fixed argv, validated ID only
        worker_command(*args),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=PROJECT_ROOT,
        **kwargs,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill(proc)
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        return WorkerResult(ok=False, error="timeout")

    if err:
        logger.warning("worker stderr: %s", err.decode("utf-8", "replace")[-500:])
    lines = [line for line in out.decode("utf-8", "replace").splitlines() if line.strip()]
    try:
        payload = json.loads(lines[-1])
    except (IndexError, ValueError):
        return WorkerResult(ok=False, error="failed")
    if not isinstance(payload, dict):
        return WorkerResult(ok=False, error="failed")
    if payload.get("ok") and isinstance(payload.get("info"), dict):
        return WorkerResult(ok=True, info=payload["info"])
    return WorkerResult(ok=False, error=str(payload.get("error") or "failed"))


def new_workdir() -> str:
    return tempfile.mkdtemp(prefix=WORKDIR_PREFIX)


def remove_workdir(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


def sweep_stale_workdirs(now: float | None = None) -> None:
    """Safety net: delete leftover work dirs (e.g. client disconnected mid-stream)."""
    now = now or time.time()
    root = Path(tempfile.gettempdir())
    for entry in root.glob(WORKDIR_PREFIX + "*"):
        try:
            if entry.is_dir() and now - entry.stat().st_mtime > STALE_WORKDIR_SECONDS:
                shutil.rmtree(entry, ignore_errors=True)
        except OSError:
            continue
