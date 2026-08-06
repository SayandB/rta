"""Intelligence router for translating natural language into PySpark code."""

from __future__ import annotations

import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError

load_dotenv()


class AgentOrchestrator:
    """Route natural language intents to executable PySpark code."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OMNIROUTE_API_KEY", "")
        self.client = AsyncOpenAI(
            api_key=self.api_key or "dummy-key",
            base_url="http://localhost:20128/v1",
        )
        self.model_name = "tllm/gemini_3_pro"

    async def translate_intent_to_spark(self, user_query: str) -> str:
        """Convert a natural language request into executable PySpark code."""
        if not user_query.strip():
            raise ValueError("User query cannot be empty")

        prompt = self._build_prompt(user_query)

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior distributed data engineer. "
                            "Return only executable PySpark code. "
                            "Do not include markdown fences or prose."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                timeout=30.0,
            )

            generated_text = getattr(response.choices[0].message, "content", "")
            return self._clean_generated_code(generated_text)
        except (OpenAIError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                "LLM request failed or timed out while translating intent"
            ) from exc

    def _build_prompt(self, user_query: str) -> str:
        return (
            "Translate the following natural language request into a single "
            "PySpark snippet that uses SparkSession and a DataFrame. "
            f"Request: {user_query}"
        )

    def _clean_generated_code(self, generated_text: str) -> str:
        code = generated_text.strip()
        code = re.sub(r"```(?:python)?\s*", "", code)
        code = re.sub(r"\s*```", "", code)
        return code.strip()
