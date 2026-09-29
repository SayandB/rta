"""Simple filesystem-backed memory layer for sessions and long-term recall."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
