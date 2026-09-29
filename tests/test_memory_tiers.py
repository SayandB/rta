"""Tests for tier-aware memory recall."""

from __future__ import annotations

import pytest

from datakernel_os.memory.store import MemorySearchResult, MemoryStore, MemoryTier


def test_tier_write_read_and_list_round_trip(tmp_path) -> None:
    store = MemoryStore(root_dir=tmp_path)

    for tier in MemoryTier:
        key = f"record-{tier.value}"
        payload = {"tier": tier.value, "value": "remember this"}

        assert store.write_tier(tier, key, payload) == payload
        assert store.read_tier(tier, key) == payload
        assert store.list_tier(tier) == [key]


def test_cross_tier_search_returns_tier_and_key(tmp_path) -> None:
    store = MemoryStore(root_dir=tmp_path)
    store.write_tier(MemoryTier.EPISODIC, "event-1", {"text": "spark job completed"})
    store.write_tier(MemoryTier.SEMANTIC, "fact-1", {"text": "spark is distributed"})
    store.write_tier(MemoryTier.ARCHIVAL, "old-1", {"text": "unrelated record"})

    matches = store.search_tiers("spark")

    assert matches == [
        MemorySearchResult(tier=MemoryTier.EPISODIC, key="event-1"),
        MemorySearchResult(tier=MemoryTier.SEMANTIC, key="fact-1"),
    ]


def test_tier_methods_preserve_legacy_scope_api(tmp_path) -> None:
    store = MemoryStore(root_dir=tmp_path)
    legacy_payload = {"kind": "runtime_event"}

    store.write(scope="session", key="legacy-1", payload=legacy_payload)

    assert store.read(scope="session", key="legacy-1") == legacy_payload
    assert store.list_scope("session") == ["legacy-1"]


def test_cross_tier_search_rejects_blank_query(tmp_path) -> None:
    store = MemoryStore(root_dir=tmp_path)

    with pytest.raises(ValueError, match="query cannot be empty"):
        store.search_tiers("  ")


def test_tier_methods_reject_unknown_tier(tmp_path) -> None:
    store = MemoryStore(root_dir=tmp_path)

    with pytest.raises(ValueError):
        store.list_tier("short-term")
