"""Secure execution runner for sandboxed Python tasks."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SandboxResult:
    """Result object for a sandboxed execution attempt."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    error: str | None = None


class SandboxRunner:
    """Execute Python snippets in an isolated working directory with bounded time."""

    def __init__(
        self, work_dir: str | Path | None = None, timeout_seconds: int = 10
    ) -> None:
        self.work_dir = Path(work_dir) if work_dir is not None else None
        self.timeout_seconds = timeout_seconds

    def run(self, code: str, timeout_seconds: int | None = None) -> SandboxResult:
        """Execute a Python snippet and return structured output."""
        timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        started = time.perf_counter()

        with tempfile.TemporaryDirectory(
            dir=str(self.work_dir) if self.work_dir else None
        ) as tmp_dir:
            try:
                completed = subprocess.run(
                    [sys.executable, "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tmp_dir,
                    env={
                        **dict(__import__("os").environ),
                        "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
                    },
                    check=False,
                )
                duration = time.perf_counter() - started
                return SandboxResult(
                    success=completed.returncode == 0,
                    exit_code=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    duration_seconds=round(duration, 4),
                )
            except subprocess.TimeoutExpired as exc:
                duration = time.perf_counter() - started
                return SandboxResult(
                    success=False,
                    exit_code=-1,
                    stdout=exc.stdout or "",
                    stderr=(exc.stderr or "")
                    + f"\nExecution timed out after {timeout} seconds",
                    duration_seconds=round(duration, 4),
                    error="timeout",
                )
