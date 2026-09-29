"""Simple filesystem-backed memory layer for sessions and long-term recall."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class MemoryTier(str, Enum):
    """Supported memory lifetimes/categories for runtime recall."""

    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    ARCHIVAL = "archival"


@dataclass(frozen=True, slots=True)
class MemorySearchResult:
    """A matching key annotated with the tier it was found in."""

    tier: MemoryTier
    key: str


class MemoryStore:
    """Store and retrieve JSON payloads in a scope-aware local storage directory."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _scope_dir(self, scope: str) -> Path:
        scope_path = self.root_dir / scope
        scope_path.mkdir(parents=True, exist_ok=True)
        return scope_path

    def _path_for(self, scope: str, key: str) -> Path:
        return self._scope_dir(scope) / f"{key}.json"

    def write(self, scope: str, key: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist a payload to disk and return the stored payload."""
        record = {
            "key": key,
            "scope": scope,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        path = self._path_for(scope, key)
        path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        return record["payload"]

    def read(self, scope: str, key: str) -> dict[str, Any]:
        """Read a stored payload by scope and key."""
        path = self._path_for(scope, key)
        if not path.exists():
            raise KeyError(f"Memory entry '{key}' not found in scope '{scope}'")
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["payload"]

    def list_scope(self, scope: str) -> list[str]:
        """List the stored memory keys for a scope."""
        scope_dir = self._scope_dir(scope)
        return sorted(item.stem for item in scope_dir.glob("*.json"))

    def search(self, scope: str, query: str) -> list[str]:
        """Simple full-text lookup inside stored JSON payloads."""
        matches: list[str] = []
        for key in self.list_scope(scope):
            payload = self.read(scope, key)
            if query.lower() in json.dumps(payload, sort_keys=True).lower():
                matches.append(key)
        return matches

    @staticmethod
    def _coerce_tier(tier: MemoryTier | str) -> MemoryTier:
        try:
            return MemoryTier(tier)
        except ValueError as exc:
            raise ValueError(f"Unknown memory tier: {tier!r}") from exc

    def write_tier(
        self, tier: MemoryTier | str, key: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Persist a record under one of the validated memory tiers."""
        normalized_tier = self._coerce_tier(tier)
        return self.write(normalized_tier.value, key, payload)

    def read_tier(self, tier: MemoryTier | str, key: str) -> dict[str, Any]:
        """Read a record from a validated memory tier."""
        normalized_tier = self._coerce_tier(tier)
        return self.read(normalized_tier.value, key)

    def list_tier(self, tier: MemoryTier | str) -> list[str]:
        """List record keys in a validated memory tier."""
        normalized_tier = self._coerce_tier(tier)
        return self.list_scope(normalized_tier.value)

    def search_tiers(
        self,
        query: str,
        tiers: Iterable[MemoryTier | str] | None = None,
    ) -> list[MemorySearchResult]:
        """Search selected tiers, returning each match with its source tier."""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Memory search query cannot be empty")

        selected_tiers = (
            tuple(MemoryTier)
            if tiers is None
            else tuple(dict.fromkeys(self._coerce_tier(tier) for tier in tiers))
        )
        return [
            MemorySearchResult(tier=tier, key=key)
            for tier in selected_tiers
            for key in self.search(tier.value, normalized_query)
        ]
