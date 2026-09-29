"""Intelligence router for translating natural language into PySpark code."""

from __future__ import annotations

import os
import re

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

    async def translate_intent_to_spark(
        self, user_query: str, schema_context: str | None = None
    ) -> str:
        """Convert a natural language request into executable PySpark code."""
        if not user_query.strip():
            raise ValueError("User query cannot be empty")

        prompt = self._build_prompt(user_query, schema_context=schema_context)

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

    async def repair_code_with_feedback(
        self,
        original_code: str,
        failure_traceback: str,
        user_query: str | None = None,
        schema_context: str | None = None,
    ) -> str:
        """Ask the model to repair code after an execution failure."""
        if not original_code.strip():
            raise ValueError("Original code cannot be empty")

        prompt = self._build_repair_prompt(
            original_code=original_code,
            failure_traceback=failure_traceback,
            user_query=user_query,
            schema_context=schema_context,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior distributed data engineer. "
                            "Return only a corrected PySpark snippet. "
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
            raise RuntimeError("LLM repair request failed") from exc

    def _build_prompt(self, user_query: str, schema_context: str | None = None) -> str:
        prompt = (
            "Translate the following natural language request into a single "
            "PySpark snippet that uses the provided dataframe namespace. "
            f"Request: {user_query}"
        )
        if schema_context:
            prompt = f"{prompt}\n\nSchema context:\n{schema_context}"
        return prompt

    def _build_repair_prompt(
        self,
        original_code: str,
        failure_traceback: str,
        user_query: str | None = None,
        schema_context: str | None = None,
    ) -> str:
        prompt = (
            "Repair the following PySpark snippet using the failure trace. "
            "Return only corrected code.\n\n"
            f"Original code:\n{original_code}\n\n"
            f"Failure traceback:\n{failure_traceback}"
        )
        if user_query:
            prompt = f"{prompt}\n\nOriginal user request:\n{user_query}"
        if schema_context:
            prompt = f"{prompt}\n\nSchema context:\n{schema_context}"
        return prompt

    def _clean_generated_code(self, generated_text: str) -> str:
        code = generated_text.strip()
        code = re.sub(r"```(?:python)?\s*", "", code)
        code = re.sub(r"\s*```", "", code)
        return code.strip()
