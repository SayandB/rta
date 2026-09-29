"""Declarative system graph for the agentic runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SystemModule:
    """A runtime module with dependency and health metadata."""

    name: str
    kind: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SystemGraph:
    """Minimal system manifest used to evolve runtime modules safely."""

    name: str = "rta"
    modules: dict[str, SystemModule] = field(default_factory=dict)

    def register(self, module: SystemModule) -> None:
        self.modules[module.name] = module

    def get(self, name: str) -> SystemModule | None:
        return self.modules.get(name)

    def active_modules(self) -> list[str]:
        return [name for name, module in self.modules.items() if module.enabled]
