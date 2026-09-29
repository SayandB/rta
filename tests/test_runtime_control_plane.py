"""Regression tests for the initial runtime control-plane modules."""

from __future__ import annotations

import json

from datakernel_os.memory.store import MemoryStore
from datakernel_os.runtime.router import OmniRouteConfig, OmniRouteRouter
from datakernel_os.sandbox.runner import SandboxRunner


def test_router_builds_payload_with_model_fallback() -> None:
    config = OmniRouteConfig(
        base_url="http://localhost:20128/v1",
        api_key="demo-key",
        default_model="tllm/gemini_3_pro",
        fallback_models=("openai/gpt-4o-mini",),
    )
    router = OmniRouteRouter(config=config)

    payload = router.build_payload(
        prompt="summarize the dataset",
        system_prompt="You are a data engineer",
        preferred_model="tllm/gemini_3_pro",
    )

    assert payload["model"] == "tllm/gemini_3_pro"
    assert payload["messages"][0]["role"] == "system"
    assert "summarize the dataset" in payload["messages"][1]["content"]


def test_memory_store_round_trips_records() -> None:
    store = MemoryStore(root_dir="/tmp/rta_memory_test")
    record = {"kind": "agent_event", "status": "ok"}

    stored = store.write(scope="session", key="run-1", payload=record)
    loaded = store.read(scope="session", key="run-1")

    assert stored["kind"] == "agent_event"
    assert loaded["kind"] == "agent_event"
    assert store.list_scope("session")


def test_sandbox_runner_executes_python_and_captures_stdout() -> None:
    runner = SandboxRunner(timeout_seconds=5)

    result = runner.run("print('hello from sandbox')\nprint(2 + 2)")

    assert result.success is True
    assert "hello from sandbox" in result.stdout
    assert result.exit_code == 0


def test_sandbox_runner_reports_failed_code() -> None:
    runner = SandboxRunner(timeout_seconds=5)

    result = runner.run("raise RuntimeError('boom')")

    assert result.success is False
    assert "boom" in result.stderr
    assert result.exit_code != 0
