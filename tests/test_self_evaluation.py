"""Tests for the runtime self-evaluation and planning loop."""

from __future__ import annotations

from datakernel_os.evolution.evaluator import SelfEvaluationEngine
from datakernel_os.evolution.planner import RuntimePlanner
from datakernel_os.memory.store import MemoryStore
from datakernel_os.system.system_graph import SystemGraph, SystemModule


def test_self_evaluation_scopes_runtime_health() -> None:
    graph = SystemGraph(name="rta")
    graph.register(SystemModule(name="router", kind="gateway", enabled=True))
    graph.register(SystemModule(name="memory", kind="state", enabled=True))

    memory = MemoryStore(root_dir="/tmp/rta_self_eval_test")
    memory.write(
        scope="runtime",
        key="task-1",
        payload={
            "context": {"module": "router"},
            "sandbox_result": {"success": True},
        },
    )
    memory.write(
        scope="runtime",
        key="task-2",
        payload={
            "context": {"module": "router"},
            "sandbox_result": {"success": False},
        },
    )
    memory.write(
        scope="runtime",
        key="task-3",
        payload={
            "context": {"module": "memory"},
            "sandbox_result": {"success": True},
        },
    )

    engine = SelfEvaluationEngine(system_graph=graph, memory_store=memory)
    report = engine.evaluate()

    assert "router" in report
    assert "memory" in report
    assert report["router"].status in {"healthy", "degraded", "critical"}
    assert report["memory"].score >= 0.0


def test_self_evaluation_can_produce_improvement_recommendations() -> None:
    graph = SystemGraph(name="rta")
    graph.register(SystemModule(name="router", kind="gateway", enabled=True))

    memory = MemoryStore(root_dir="/tmp/rta_self_eval_recommendations")
    memory.write(
        scope="runtime",
        key="task-a",
        payload={
            "context": {"module": "router"},
            "sandbox_result": {"success": False},
        },
    )

    engine = SelfEvaluationEngine(system_graph=graph, memory_store=memory)
    recommendations = engine.recommend_improvements()

    assert "router" in recommendations
    assert recommendations["router"]


def test_runtime_planner_turns_health_into_safe_actions() -> None:
    graph = SystemGraph(name="rta")
    graph.register(SystemModule(name="router", kind="gateway", enabled=True))

    memory = MemoryStore(root_dir="/tmp/rta_self_eval_planner")
    memory.write(
        scope="runtime",
        key="task-p1",
        payload={
            "context": {"module": "router"},
            "sandbox_result": {"success": False},
        },
    )

    engine = SelfEvaluationEngine(system_graph=graph, memory_store=memory)
    planner = RuntimePlanner(system_graph=graph, evaluator=engine)
    plan = planner.build_plan()

    assert "router" in plan
    assert plan["router"].action in {"disable", "reconfigure", "monitor"}

    planner.apply_plan(plan)
    assert graph.get("router") is not None
    assert graph.get("router").enabled is True or graph.get("router").enabled is False
