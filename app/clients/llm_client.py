from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Protocol, Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


class LLMClientError(RuntimeError):
    """Raised when the LLM client fails to complete a generation request."""


class LLMClient(Protocol):
    """Contract for all LLM client implementations."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str:
        """Return generated text from the underlying model."""
        ...


@dataclass(frozen=True)
class MockLLMClient:
    """
    Deterministic local fallback.

    This allows Phase 1 development without any provider dependency.
    """

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str:
        del user_prompt, temperature

        if "Return only a JSON array" in system_prompt:
            return """
[
  {
    "fact": "The provided sources describe the topic from an engineering and systems perspective.",
    "source_url": "https://example.com/overview",
    "source_title": "Mock extracted fact",
    "fact_type": "claim",
    "evidence_snippet": "Overview source for the topic, including practical implications and tradeoffs.",
    "confidence": "medium"
  }
]
""".strip()

        if '"context": "string"' in system_prompt:
            return """
{
  "context": "This topic matters because it affects how teams design and validate technical systems.",
  "insights": [
    "The topic is repeatedly framed in terms of engineering tradeoffs.",
    "System design and credibility are closely connected.",
    "Practical implementation details matter as much as conceptual framing."
  ],
  "implications": [
    "Teams benefit from stronger validation and evidence preservation.",
    "Architectural choices shape output quality and trust."
  ],
  "contrarian_angle": "The core challenge is often not generation speed but controlling how evidence is transformed."
}
""".strip()

        if "technical content drafting engine" in system_prompt.lower():
            return """
One thing that stands out to me:

This topic matters because it affects how teams design and validate technical systems.

A few signals keep showing up:
- The topic is repeatedly framed in terms of engineering tradeoffs.
- System design and credibility are closely connected.
- Practical implementation details matter as much as conceptual framing.

What matters in practice is simple:
teams need stronger validation and better evidence preservation.

That is usually where stronger systems separate themselves from shallow workflows.
""".strip()

        if '"ok": true' in system_prompt and "draft" in system_prompt:
            return """
{
  "ok": true,
  "issues": []
}
""".strip()

        if "style rewriting engine" in system_prompt.lower():
            return """
One thing I keep noticing:

The interesting part of this topic is not just the idea itself.

It is what happens when teams try to make it real.

A few patterns show up quickly:
- engineering tradeoffs shape the outcome
- credibility depends on preserving evidence
- implementation details matter more than abstract claims

What actually matters is whether the system can stay grounded while it transforms information.

That is where stronger pipelines start to look different.
""".strip()

        if '"ok": true' in system_prompt and "styled post" in system_prompt.lower():
            return """
{
  "ok": true,
  "issues": []
}
""".strip()

        return "MOCK_RESPONSE"


@dataclass(frozen=True)
class OpenAICompatibleLLMClient:
    """
    Minimal OpenAI-compatible HTTP client.

    Supports:
    - OpenAI-style APIs
    - local vLLM OpenAI-compatible endpoints later
    - explicit, testable interface
    """

    api_key: str
    base_url: str = "https://api.openai.com/v1/responses"
    model: str = "gpt-4.1-mini"
    timeout_seconds: int = 30

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str:
        if requests is None:
            raise LLMClientError(
                "requests is not installed. Add it to dependencies before using OpenAICompatibleLLMClient."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_output_tokens": 1024,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            if response.status_code >= 400:
                 print("\n=== OPENAI ERROR BODY ===")
                 print(response.text)
                 print("=== END ERROR BODY ===\n")
            response.raise_for_status()
        except Exception as exc:
            raise LLMClientError(f"LLM request failed: {exc}") from exc

        data = response.json()

        try:
            content = data["output_text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("LLM response format was invalid.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMClientError("LLM response content was empty.")

        return content.strip()


def get_llm_client() -> LLMClient:
    """
    Factory for selecting an LLM client.

    Phase 1 behavior:
    - use OpenAI-compatible client if OPENAI_API_KEY exists
    - otherwise use mock client for unblockable local iteration
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        return OpenAICompatibleLLMClient(api_key=api_key)

    return MockLLMClient()
