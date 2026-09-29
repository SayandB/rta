"""OmniRoute-compatible gateway adapter for local model routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OmniRouteConfig:
    """Configuration for the local AI gateway."""

    base_url: str = "http://localhost:20128/v1"
    api_key: str = "dummy-key"
    default_model: str = "tllm/gemini_3_pro"
    fallback_models: tuple[str, ...] = ()
    timeout_seconds: float = 30.0
    max_retries: int = 2
    compression_enabled: bool = True


class OmniRouteRouter:
    """Thin adapter that normalizes model routing decisions for local gateways."""

    def __init__(self, config: OmniRouteConfig | None = None) -> None:
        self.config = config or OmniRouteConfig()

    def choose_model(self, preferred_model: str | None = None) -> str:
        """Return the best available model for the active request."""
        candidates = [
            preferred_model,
            self.config.default_model,
            *self.config.fallback_models,
        ]
        for model in candidates:
            if model:
                return model
        raise ValueError("No valid model configuration is available for OmniRoute")

    def build_payload(
        self,
        prompt: str,
        system_prompt: str,
        preferred_model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Create a structured OpenAI-compatible payload for the gateway."""
        payload: dict[str, Any] = {
            "model": self.choose_model(preferred_model),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return payload

    def health_check(self) -> dict[str, Any]:
        """Return router metadata for startup and operational checks."""
        return {
            "status": "ok",
            "base_url": self.config.base_url,
            "default_model": self.config.default_model,
            "fallback_models": list(self.config.fallback_models),
            "compression_enabled": self.config.compression_enabled,
        }

    def route(
        self,
        prompt: str,
        system_prompt: str,
        preferred_model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Convenience method for use by orchestrators and higher-level agent loops."""
        return self.build_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            preferred_model=preferred_model,
            **kwargs,
        )
