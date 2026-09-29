"""Tests for the economic and scaling rails."""

from __future__ import annotations

from datakernel_os.economics import BudgetPolicy, Wallet
from datakernel_os.scale import ScaleDecision, ScaleEngine, ScalePolicy


def test_wallet_tracks_credit_and_debit() -> None:
    wallet = Wallet(starting_balance=100.0)

    wallet.credit(25.0)
    wallet.debit(40.0, reason="task-run")

    assert wallet.balance == 85.0
    assert wallet.transactions[-1]["reason"] == "task-run"


def test_scale_policy_recommends_growth_under_load() -> None:
    policy = ScalePolicy(max_budget=250.0, min_budget=25.0, burst_factor=1.5, scale_step=25.0)

    decision = policy.decide(balance=220.0, load=0.82, active_workers=2)

    assert decision.action == "scale_out"
    assert decision.budget_delta == 25.0


def test_scale_engine_restricts_expansion_when_budget_is_constrained() -> None:
    policy = ScalePolicy(max_budget=200.0, min_budget=25.0, burst_factor=1.0, scale_step=25.0)
    engine = ScaleEngine(policy=policy)

    decision = engine.decide(balance=15.0, load=0.9, active_workers=4)

    assert decision.action == "scale_in"
    assert isinstance(decision, ScaleDecision)
