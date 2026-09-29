"""Tests for browser and OSINT observation adapters."""

from __future__ import annotations

from datakernel_os.observation import (
    BrowserObservationAdapter,
    ObservationRecord,
    OSINTObservationAdapter,
    normalize_observation,
)


def test_browser_adapter_creates_normalized_observation() -> None:
    adapter = BrowserObservationAdapter()

    record = adapter.collect(url="https://example.com", content="Example text from a page")

    assert isinstance(record, ObservationRecord)
    assert record.source == "browser"
    assert record.payload["url"] == "https://example.com"
    assert record.payload["summary"]
    assert "example" in record.payload["summary"].lower()


def test_osint_adapter_normalizes_external_signal() -> None:
    adapter = OSINTObservationAdapter()

    record = adapter.collect(query="openai launch", result={"title": "OpenAI Launch", "signals": ["pricing", "reliability"]})

    assert record.source == "osint"
    assert record.payload["title"] == "OpenAI Launch"
    assert record.payload["signals"] == ["pricing", "reliability"]


def test_normalize_observation_preserves_rich_context() -> None:
    record = normalize_observation({
        "source": "browser",
        "url": "https://example.com",
        "content": "Example page for the runtime",
    })

    assert record.source == "browser"
    assert record.payload["url"] == "https://example.com"
    assert "runtime" in record.payload["summary"].lower()
