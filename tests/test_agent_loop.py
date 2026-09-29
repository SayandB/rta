"""Tests for the runtime agent loop."""

from __future__ import annotations

from datakernel_os.runtime.agent_loop import AgentLoop


def test_agent_loop_persists_runtime_task() -> None:
    loop = AgentLoop(storage_root="/tmp/rta_agent_loop_test")

    result = loop.run(
        "summarize the current task state",
        system_prompt="You are a systems architect.",
        code="print('agent loop ok')",
        context={"module": "runtime"},
    )

    assert result.task_id
    assert result.payload["model"]
    assert result.sandbox_result is not None
    assert result.sandbox_result.success is True
    assert result.memory_key

    stored = loop.memory_store.read(scope="runtime", key=result.memory_key)
    assert stored["prompt"] == "summarize the current task state"
