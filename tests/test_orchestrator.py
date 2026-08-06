"""Tests for the orchestrator translation layer."""

from __future__ import annotations

import pytest

from datakernel_os.core.orchestrator import AgentOrchestrator


@pytest.mark.asyncio
async def test_clean_generated_code_removes_markdown_fences() -> None:
    orchestrator = AgentOrchestrator(api_key="test-key")

    cleaned = orchestrator._clean_generated_code("```python\nprint('hello')\n```")

    assert cleaned == "print('hello')"


def test_build_prompt_includes_user_query() -> None:
    orchestrator = AgentOrchestrator(api_key="test-key")

    prompt = orchestrator._build_prompt("summarize sales")

    assert "summarize sales" in prompt
    assert "PySpark" in prompt
