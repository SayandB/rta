"""Safe, bounded task verification from a machine-readable JSON backlog."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

VerificationCommand = list[str]
RemediationHandler = Callable[[dict[str, Any], str], bool]


class BacklogRunner:
    """Run one allowlisted task at a time and persist each state transition."""

    ALLOWED_COMMANDS = frozenset(
        {
            ("python", "-m", "ruff", "check", "src", "tests"),
            ("python", "-m", "ruff", "format", "--check", "src", "tests"),
            ("pytest", "-q", "tests/test_runtime_control_plane.py"),
            ("pytest", "-q"),
        }
    )
    MAX_RETRIES = 3
    OUTPUT_LIMIT = 4000

    def __init__(
        self,
        backlog_path: str | Path,
        *,
        max_retries: int = MAX_RETRIES,
        timeout_seconds: int = 300,
        remediation_handler: RemediationHandler | None = None,
    ) -> None:
        if not 0 <= max_retries <= self.MAX_RETRIES:
            raise ValueError(f"max_retries must be between 0 and {self.MAX_RETRIES}")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.backlog_path = Path(backlog_path)
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.remediation_handler = remediation_handler

    def _load(self) -> dict[str, Any]:
        try:
            backlog = json.loads(self.backlog_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Unable to read backlog: {self.backlog_path}") from exc
        if not isinstance(backlog, dict) or not isinstance(backlog.get("tasks"), list):
            raise ValueError("Backlog must be a JSON object with a tasks array")
        return backlog

    def _save(self, backlog: dict[str, Any]) -> None:
        self.backlog_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.backlog_path.parent,
                prefix=f".{self.backlog_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                json.dump(backlog, temporary_file, indent=2, sort_keys=True)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            Path(temporary_path).replace(self.backlog_path)
        finally:
            if temporary_path and Path(temporary_path).exists():
                Path(temporary_path).unlink()

    def _validate_commands(self, task: dict[str, Any]) -> list[VerificationCommand]:
        commands = task.get("verification_commands")
        if not isinstance(commands, list) or not commands:
            raise ValueError("Each task needs at least one verification command")
        validated: list[VerificationCommand] = []
        for command in commands:
            if not isinstance(command, list) or not all(
                isinstance(argument, str) for argument in command
            ):
                raise ValueError(
                    "Verification commands must be arrays of string arguments"
                )
            if tuple(command) not in self.ALLOWED_COMMANDS:
                raise ValueError(
                    f"Verification command is not allowlisted: {command!r}"
                )
            validated.append(command)
        return validated

    def _verify(self, task: dict[str, Any]) -> tuple[bool, str]:
        output: list[str] = []
        for command in self._validate_commands(task):
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or ""
                stderr = exc.stderr or ""
                if isinstance(stdout, bytes):
                    stdout = stdout.decode(errors="replace")
                if isinstance(stderr, bytes):
                    stderr = stderr.decode(errors="replace")
                return False, (
                    "\n".join([*output, stdout, stderr, "Verification timed out"])[
                        -self.OUTPUT_LIMIT :
                    ]
                )
            output.append(
                f"$ {' '.join(command)}\n{completed.stdout}{completed.stderr}"
            )
            if completed.returncode != 0:
                return False, "\n".join(output)[-self.OUTPUT_LIMIT :]
        return True, "\n".join(output)[-self.OUTPUT_LIMIT :]

    def run_next(self) -> dict[str, Any] | None:
        """Verify the next pending task; leave commits and pushes to human review."""
        backlog = self._load()
        task = next(
            (item for item in backlog["tasks"] if item.get("status") == "pending"), None
        )
        if task is None:
            return None
        if not isinstance(task.get("id"), str) or not task["id"].strip():
            raise ValueError("Every backlog task needs a non-empty id")

        task["status"] = "running"
        task["attempts"] = 0
        self._save(backlog)

        while True:
            task["attempts"] += 1
            try:
                passed, output = self._verify(task)
            except ValueError as exc:
                passed, output = False, str(exc)
            task["last_output"] = output[-self.OUTPUT_LIMIT :]
            if passed:
                task["status"] = "completed"
                self._save(backlog)
                return task

            retries_used = task["attempts"] - 1
            if retries_used >= self.max_retries or self.remediation_handler is None:
                task["status"] = "blocked"
                self._save(backlog)
                return task

            try:
                repaired = self.remediation_handler(task, task["last_output"])
            except Exception as exc:  # noqa: BLE001 - Prevent callback errors from escaping the bounded runner.
                task["last_output"] = (
                    f"{task['last_output']}\nRemediation failed: {exc}"[
                        -self.OUTPUT_LIMIT :
                    ]
                )
                repaired = False
            if not repaired:
                task["status"] = "blocked"
                self._save(backlog)
                return task
            self._save(backlog)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", default="backlog.json", type=Path)
    arguments = parser.parse_args()
    try:
        task = BacklogRunner(arguments.backlog).run_next()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if task is None:
        print("No pending backlog tasks.")
        return 0
    print(
        f"{task['id']}: {task['status']} after {task['attempts']} verification attempt(s)"
    )
    if task["status"] != "completed":
        print(task.get("last_output", ""), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
