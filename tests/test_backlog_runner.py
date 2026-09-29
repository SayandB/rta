"""Tests for the bounded backlog verification runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from datakernel_os.autonomy.backlog import BacklogRunner


def _write_backlog(path: Path, command: list[str]) -> None:
    path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "T-TEST",
                        "description": "Run a real targeted verification",
                        "verification_commands": [command],
                        "status": "pending",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_runner_marks_task_complete_after_real_verification(tmp_path: Path) -> None:
    backlog_path = tmp_path / "backlog.json"
    _write_backlog(
        backlog_path, ["pytest", "-q", "tests/test_runtime_control_plane.py"]
    )

    task = BacklogRunner(backlog_path=backlog_path).run_next()

    assert task is not None
    assert task["status"] == "completed"
    assert task["attempts"] == 1
    persisted = json.loads(backlog_path.read_text(encoding="utf-8"))
    assert persisted["tasks"][0]["status"] == "completed"


def test_runner_rejects_shell_commands_and_fails_closed(tmp_path: Path) -> None:
    backlog_path = tmp_path / "backlog.json"
    _write_backlog(backlog_path, ["sh", "-c", "echo unsafe"])

    task = BacklogRunner(backlog_path=backlog_path).run_next()

    assert task is not None
    assert task["status"] == "blocked"
    assert "not allowlisted" in task["last_output"]


def test_runner_caps_retries_at_three(tmp_path: Path) -> None:
    backlog_path = tmp_path / "backlog.json"
    _write_backlog(backlog_path, ["pytest", "-q", "tests/does_not_exist.py"])

    with pytest.raises(ValueError, match="max_retries"):
        BacklogRunner(backlog_path=backlog_path, max_retries=4)


def test_runner_stops_after_three_remediation_retries(tmp_path: Path) -> None:
    backlog_path = tmp_path / "backlog.json"
    _write_backlog(backlog_path, ["pytest", "-q", "tests/does_not_exist.py"])
    remediation_calls = 0

    def report_repair_applied(task: dict[str, object], output: str) -> bool:
        nonlocal remediation_calls
        remediation_calls += 1
        return True

    task = BacklogRunner(
        backlog_path=backlog_path,
        max_retries=3,
        remediation_handler=report_repair_applied,
    ).run_next()

    assert task is not None
    assert task["status"] == "blocked"
    assert task["attempts"] == 4
    assert remediation_calls == 3
