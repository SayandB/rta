"""Scale decisions driven by load and cost guardrails."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScaleDecision:
    """One guarded action proposed by the scale engine."""

    action: str
    reason: str
    active_workers: int
    budget_delta: float = 0.0
    scale_factor: float = 1.0


@dataclass(slots=True)
class ScalePolicy:
    """Conservative scaling policy for runtime expansion or contraction."""

    max_budget: float = 250.0
    min_budget: float = 25.0
    burst_factor: float = 1.5
    scale_step: float = 25.0
    load_threshold: float = 0.75
    min_workers: int = 1

    def decide(self, *, balance: float, load: float, active_workers: int) -> ScaleDecision:
        if balance <= self.min_budget:
            return ScaleDecision(
                action="scale_in",
                reason="Budget is below minimum guardrail; constrain execution.",
                active_workers=max(self.min_workers, active_workers - 1),
                budget_delta=-self.scale_step,
                scale_factor=0.75,
            )

        if load >= self.load_threshold and balance < self.max_budget:
            return ScaleDecision(
                action="scale_out",
                reason="Load is elevated and budget headroom remains available.",
                active_workers=max(self.min_workers, active_workers + 1),
                budget_delta=min(self.scale_step, self.max_budget - balance),
                scale_factor=self.burst_factor,
            )

        if load < 0.35 and balance > self.max_budget * 0.9:
            return ScaleDecision(
                action="scale_in",
                reason="Low load and budget pressure suggest contraction.",
                active_workers=max(self.min_workers, active_workers - 1),
                budget_delta=-self.scale_step,
                scale_factor=0.8,
            )

        return ScaleDecision(
            action="hold",
            reason="Within policy guardrails; preserve current scale.",
            active_workers=active_workers,
            budget_delta=0.0,
            scale_factor=1.0,
        )


class ScaleEngine:
    """Facade for evaluating scale decisions against runtime policy."""

    def __init__(self, policy: ScalePolicy | None = None) -> None:
        self.policy = policy or ScalePolicy()

    def decide(self, *, balance: float, load: float, active_workers: int) -> ScaleDecision:
        return self.policy.decide(balance=balance, load=load, active_workers=active_workers)
