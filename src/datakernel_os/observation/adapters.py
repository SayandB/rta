"""Normalized observation adapters for browser and OSINT signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class ObservationRecord:
    """A normalized runtime observation from an external signal source."""

    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "payload": self.payload,
            "captured_at": self.captured_at,
        }


def _summarize_text(content: str | None, fallback: str | None = None) -> str:
    text = (content or fallback or "").strip()
    if not text:
        return "No observation content captured."
    cleaned = " ".join(text.split())
    if len(cleaned) <= 180:
        return cleaned
    return cleaned[:177].rstrip() + "..."


class BrowserObservationAdapter:
    """Capture browser-style observations and normalize them as runtime telemetry."""

    def collect(self, url: str, content: str | None = None, **metadata: Any) -> ObservationRecord:
        payload: dict[str, Any] = {
            "url": url,
            "content": content or "",
            "summary": _summarize_text(content, fallback=url),
        }
        payload.update(metadata)
        return ObservationRecord(source="browser", payload=payload)


class OSINTObservationAdapter:
    """Normalize open-source intelligence or external signal snippets."""

    def collect(self, query: str, result: dict[str, Any] | None = None, **metadata: Any) -> ObservationRecord:
        signal = result or {}
        payload: dict[str, Any] = {
            "query": query,
            "title": signal.get("title") or query,
            "signals": list(signal.get("signals") or signal.get("items") or []),
            "summary": _summarize_text(signal.get("summary") or signal.get("content") or str(signal), fallback=f"OSINT summary for: {query}"),
        }
        payload.update({key: value for key, value in metadata.items() if value is not None})
        return ObservationRecord(source="osint", payload=payload)


def normalize_observation(value: ObservationRecord | dict[str, Any]) -> ObservationRecord:
    """Convert raw observation payloads into a standard ObservationRecord."""
    if isinstance(value, ObservationRecord):
        return value
    source = str(value.get("source") or "unknown")
    payload = value.get("payload") or value
    if isinstance(payload, dict):
        normalized_payload = dict(payload)
    else:
        normalized_payload = {"value": payload}
    if "summary" not in normalized_payload:
        normalized_payload["summary"] = _summarize_text(
            normalized_payload.get("content") or normalized_payload.get("summary"),
            fallback=normalized_payload.get("url") or normalized_payload.get("query") or source,
        )
    return ObservationRecord(source=source, payload=normalized_payload)
