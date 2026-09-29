"""Self-evaluation and evolution primitives for the autonomous runtime."""

from .evaluator import SelfEvaluationEngine, TelemetrySignal
from .planner import EvolutionRecommendation, RuntimePlanner

__all__ = [
    "EvolutionRecommendation",
    "RuntimePlanner",
    "SelfEvaluationEngine",
    "TelemetrySignal",
]
