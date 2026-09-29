"""Minimal agent execution loop for the autonomous runtime kernel."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from datakernel_os.memory.store import MemoryStore
from datakernel_os.runtime.router import OmniRouteConfig, OmniRouteRouter
from datakernel_os.sandbox.runner import SandboxResult, SandboxRunner
from datakernel_os.system.system_graph import SystemGraph, SystemModule


@dataclass(slots=True)
class AgentTask:
    """Definition of a task sent to the agent runtime."""

    prompt: str
    system_prompt: str = "You are a focused autonomous systems agent."
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: dict[str, Any] = field(default_factory=dict)
    code: str | None = None


@dataclass(slots=True)
class AgentTaskResult:
    """Structured result emitted by the agent loop."""

    task_id: str
    payload: dict[str, Any]
    sandbox_result: SandboxResult | None = None
    memory_key: str | None = None


class AgentLoop:
    """Persisted execution loop that combines routing, memory, and sandbox evaluation."""

    def __init__(
        self,
        router: OmniRouteRouter | None = None,
        memory_store: MemoryStore | None = None,
        sandbox_runner: SandboxRunner | None = None,
        system_graph: SystemGraph | None = None,
        storage_root: str | None = None,
    ) -> None:
        self.router = router or OmniRouteRouter(config=OmniRouteConfig())
        self.memory_store = memory_store or MemoryStore(root_dir=storage_root or "/tmp/rta_runtime_memory")
        self.sandbox_runner = sandbox_runner or SandboxRunner(timeout_seconds=10)
        self.system_graph = system_graph or SystemGraph(name="rta")
        self._register_default_modules()

    def _register_default_modules(self) -> None:
        for module_name, kind in {
            "router": "gateway",
            "memory": "state",
            "sandbox": "execution",
            "orchestrator": "planning",
            "observer": "intelligence",
            "wallet": "economics",
        }.items():
            self.system_graph.register(SystemModule(name=module_name, kind=kind, enabled=True))

    def run(self, prompt: str, system_prompt: str | None = None, *, code: str | None = None, context: dict[str, Any] | None = None) -> AgentTaskResult:
        """Run a single task and persist the request/response in memory."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        task = AgentTask(
            prompt=prompt.strip(),
            system_prompt=system_prompt or "You are a focused autonomous systems agent.",
            context=context or {},
            code=code,
        )

        payload = self.router.route(
            prompt=task.prompt,
            system_prompt=task.system_prompt,
            preferred_model=self.router.config.default_model,
        )

        sandbox_result: SandboxResult | None = None
        if task.code:
            sandbox_result = self.sandbox_runner.run(task.code)

        memory_key = f"task-{task.task_id}"
        self.memory_store.write(
            scope="runtime",
            key=memory_key,
            payload={
                "task_id": task.task_id,
                "prompt": task.prompt,
                "system_prompt": task.system_prompt,
                "context": task.context,
                "payload": payload,
                "sandbox_result": None if sandbox_result is None else {
                    "success": sandbox_result.success,
                    "exit_code": sandbox_result.exit_code,
                    "stdout": sandbox_result.stdout,
                    "stderr": sandbox_result.stderr,
                    "duration_seconds": sandbox_result.duration_seconds,
                },
            },
        )

        return AgentTaskResult(
            task_id=task.task_id,
            payload=payload,
            sandbox_result=sandbox_result,
            memory_key=memory_key,
        )
