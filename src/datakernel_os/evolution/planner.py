"""Planner for evolving the system graph based on runtime evaluations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from datakernel_os.evolution.evaluator import ModuleEvaluation, SelfEvaluationEngine
from datakernel_os.system.system_graph import SystemGraph


@dataclass(slots=True)
class EvolutionRecommendation:
    """A safe runtime change proposed by the planner."""

    module: str
    action: str
    reason: str
    confidence: float
    configuration: dict[str, Any] = field(default_factory=dict)


class RuntimePlanner:
    """Maps evaluation results to conservative changes in the system graph."""

    def __init__(self, system_graph: SystemGraph | None = None, evaluator: SelfEvaluationEngine | None = None) -> None:
        self.system_graph = system_graph or SystemGraph(name="rta")
        self.evaluator = evaluator or SelfEvaluationEngine(system_graph=self.system_graph)

    def _recommend_for(self, module: str, evaluation: ModuleEvaluation) -> EvolutionRecommendation:
        if evaluation.status == "critical":
            return EvolutionRecommendation(
                module=module,
                action="disable",
                reason=f"Module '{module}' is critical; it should be disabled until trust is restored.",
                confidence=0.95,
                configuration={"enabled": False, "review_required": True},
            )

        if evaluation.status == "degraded":
            return EvolutionRecommendation(
                module=module,
                action="reconfigure",
                reason=f"Module '{module}' is degraded; increase observation and reduce execution breadth.",
                confidence=0.8,
                configuration={"enabled": True, "monitoring": True, "review_required": True},
            )

        return EvolutionRecommendation(
            module=module,
            action="monitor",
            reason=f"Module '{module}' is healthy; continue monitoring and preserve the current settings.",
            confidence=0.7,
            configuration={"enabled": True, "monitoring": True},
        )

    def build_plan(self) -> dict[str, EvolutionRecommendation]:
        """Generate a conservative action plan from the latest evaluation snapshot."""
        evaluations = self.evaluator.evaluate()
        return {module: self._recommend_for(module, evaluation) for module, evaluation in evaluations.items()}

    def apply_plan(self, plan: dict[str, EvolutionRecommendation] | None = None) -> dict[str, SystemGraph]:
        """Apply the plan to the system graph while preserving safe default settings."""
        planned = plan or self.build_plan()
        updated: dict[str, SystemGraph] = {}

        for module_name, recommendation in planned.items():
            module = self.system_graph.get(module_name)
            if module is None:
                continue

            if recommendation.action == "disable":
                module.enabled = False
            elif recommendation.action == "reconfigure":
                module.enabled = True
                module.config.update(recommendation.configuration)
            else:
                module.enabled = True
                module.config.update({"monitoring": True})

            self.system_graph.register(module)
            updated[module_name] = self.system_graph

        return updated
