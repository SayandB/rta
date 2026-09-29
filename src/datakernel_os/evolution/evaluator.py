"""Self-evaluation engine for the autonomous runtime."""

from __future__ import annotations

from dataclasses import dataclass, field

from datakernel_os.memory.store import MemoryStore
from datakernel_os.system.system_graph import SystemGraph


@dataclass(slots=True)
class TelemetrySignal:
    """A single runtime observation captured for evaluation."""

    module: str
    metric: str
    value: float
    timestamp: str | None = None


@dataclass(slots=True)
class ModuleEvaluation:
    """Aggregated view of a module's performance within the current runtime."""

    module: str
    score: float
    samples: int
    success_rate: float
    status: str
    recommendations: list[str] = field(default_factory=list)


class SelfEvaluationEngine:
    """Synthesizes runtime telemetry into safe, actionable structural recommendations."""

    def __init__(
        self,
        system_graph: SystemGraph | None = None,
        memory_store: MemoryStore | None = None,
    ) -> None:
        self.system_graph = system_graph or SystemGraph(name="rta")
        self.memory_store = memory_store or MemoryStore(
            root_dir="/tmp/rta_runtime_memory"
        )

    def record_signal(
        self, module: str, metric: str, value: float, timestamp: str | None = None
    ) -> TelemetrySignal:
        """Record a scalar signal for a subsystem and return the observation."""
        signal = TelemetrySignal(
            module=module, metric=metric, value=value, timestamp=timestamp
        )
        self.memory_store.write(
            scope="telemetry",
            key=f"{module}-{metric}-{signal.timestamp or 'now'}",
            payload={
                "module": signal.module,
                "metric": signal.metric,
                "value": signal.value,
                "timestamp": signal.timestamp,
            },
        )
        return signal

    def evaluate(self) -> dict[str, ModuleEvaluation]:
        """Summarize active modules using the persisted runtime task history."""
        module_scores: dict[str, ModuleEvaluation] = {}

        runtime_events = []
        for key in self.memory_store.list_scope("runtime"):
            try:
                runtime_events.append(self.memory_store.read("runtime", key))
            except KeyError:
                continue

        for module_name in self.system_graph.active_modules():
            module_events = [
                event
                for event in runtime_events
                if (event.get("context") or {}).get("module") == module_name
                or event.get("module") == module_name
            ]
            if not module_events:
                module_scores[module_name] = ModuleEvaluation(
                    module=module_name,
                    score=0.8,
                    samples=0,
                    success_rate=0.0,
                    status="healthy",
                    recommendations=[
                        "No runtime telemetry available; continue monitoring."
                    ],
                )
                continue

            pass_count = 0
            for event in module_events:
                sandbox = event.get("sandbox_result") or {}
                if sandbox.get("success") is True:
                    pass_count += 1

            success_rate = pass_count / len(module_events) if module_events else 0.0
            score = round(success_rate, 3)
            status = (
                "healthy"
                if score >= 0.8
                else "degraded"
                if score >= 0.5
                else "critical"
            )
            recommendations: list[str] = []
            if score < 0.8:
                recommendations.append(
                    f"Module '{module_name}' needs targeted diagnostics and safer execution constraints."
                )

            module_scores[module_name] = ModuleEvaluation(
                module=module_name,
                score=score,
                samples=len(module_events),
                success_rate=success_rate,
                status=status,
                recommendations=recommendations,
            )

        return module_scores

    def recommend_improvements(self) -> dict[str, list[str]]:
        """Return module-specific improvement actions identified by the evaluation pass."""
        recommendations: dict[str, list[str]] = {}
        for name, evaluation in self.evaluate().items():
            if evaluation.status != "healthy":
                recommendations[name] = evaluation.recommendations or [
                    f"Review module '{name}' and confirm the runtime contract remains valid."
                ]
        return recommendations
