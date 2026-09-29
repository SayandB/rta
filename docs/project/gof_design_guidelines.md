# GOF-aligned design and optimization guidelines

The runtime should prioritize clean, explicit abstractions over clever shortcuts. The goal is maintainability, deterministic behavior, and safe extension with minimal unnecessary coupling.

## Core principles

1. Prefer small, single-responsibility modules.
2. Favor composition over inheritance when the behavior is dynamic.
3. Use explicit interfaces or protocol-like boundaries to keep runtime components loosely coupled.
4. Keep state transitions explicit and auditable.
5. Optimize for clarity first, then optimize for cost where evidence shows a bottleneck.

## Recommended patterns

### Creational

- Factory: use when runtime components are chosen by policy, environment, or deployment mode.
- Builder: use for configuration-heavy runtime objects with many optional settings.
- Prototype: use for copying known-safe runtime templates when cloning configuration is simpler than reconstructing it.

### Structural

- Adapter: use to normalize gateway, memory, and observation sources behind a standard interface.
- Facade: use to present a simple API to the rest of the runtime while hiding internal complexity.
- Composite: use for logical groups of modules, tasks, or execution steps in a runtime graph.
- Decorator: use to add monitoring, tracing, or policy wrappers without modifying the base component.
- Proxy: use to represent secure or remote runtime boundaries and control access.

### Behavioral

- Strategy: use for pluggable routing, execution, or evaluation policies.
- Observer: use to broadcast runtime health and telemetry to evaluators and planners.
- Command: use for task invocations that should be logged, retried, or audited.
- Template method: use for multi-step execution flows with stable structure and variable leaf behavior.
- State: use for module health transitions such as healthy, degraded, critical.

## Optimization rules

- Use dataclasses for configuration and value objects when structure matters more than behavior.
- Avoid mutable global state for runtime configuration.
- Keep hot loops deterministic and avoid repeated recomputation.
- Validate environment and input early to fail fast.
- Use narrow interfaces and limit cross-module imports.
- Cache only when the value is expensive and reused; otherwise prefer simplicity.
- Prefer explicit error handling over silent fallbacks in production paths.

## Anti-patterns to avoid

- God objects that own routing, execution, storage, and policy logic together.
- Hidden shared mutable state across agents.
- Deep inheritance chains that make runtime behavior difficult to reason about.
- Repeated string building in hot paths.
- Excessive abstraction with no concrete use case.

## Review rubric

Every review should check:

- Does the design map to a clear GOF pattern or a justified simpler alternative?
- Does the implementation communicate intent without unnecessary indirection?
- Are the critical paths straightforward, testable, and constrained by guardrails?
- Is the code optimized for maintainability, not only cleverness?
