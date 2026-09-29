"""Budget ledger and accounting primitives for runtime tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class BudgetPolicy:
    """Simple guardrail policy for execution budgets."""

    max_budget: float = 250.0
    min_budget: float = 25.0
    scale_step: float = 25.0


class Wallet:
    """Tracks money-like runtime budget for agent execution."""

    def __init__(self, starting_balance: float = 0.0) -> None:
        self.balance = float(starting_balance)
        self.transactions: list[dict[str, Any]] = []

    def credit(self, amount: float, *, reason: str = "credit") -> float:
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        self.balance += amount
        self.transactions.append(
            {
                "direction": "credit",
                "amount": float(amount),
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return self.balance

    def debit(self, amount: float, *, reason: str = "debit") -> float:
        if amount <= 0:
            raise ValueError("Debit amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds for requested debit")
        self.balance -= amount
        self.transactions.append(
            {
                "direction": "debit",
                "amount": float(amount),
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return self.balance

    def can_afford(self, amount: float) -> bool:
        return amount <= self.balance

    def spend(self, amount: float, *, reason: str = "spend") -> float:
        return self.debit(amount, reason=reason)
