from __future__ import annotations

from app.clients.llm_client import LLMClientError
from app.clients.search_client import SearchClientError
from app.state import create_initial_state
from app.steps.extract_facts import extract_facts
from app.steps.generate_image_prompts import generate_image_prompts
from app.steps.search_web import search_web


class FailingSearchClient:
    def search(self, topic: str, top_k: int):
        raise SearchClientError("synthetic search failure")


class InvalidJsonLLMClient:
    def generate(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        return "this is not valid json"


class FailingLLMClient:
    def generate(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        raise LLMClientError("synthetic llm failure")


def test_search_web_handles_provider_failure(monkeypatch) -> None:
    monkeypatch.setattr("app.steps.search_web.get_search_client", lambda: FailingSearchClient())

    state = create_initial_state("KV-aware routing")
    result = search_web(state)

    assert result["raw"]["search_results"] == []
    assert result["sources"] == []
    assert len(result["errors"]) >= 1
    assert any(issue["step"] == "search_web" for issue in result["validation"]["issues"])


def test_extract_facts_falls_back_when_llm_returns_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr("app.steps.extract_facts.get_llm_client", lambda: InvalidJsonLLMClient())

    state = create_initial_state("LLM inference routing")
    state["raw"]["search_results"] = [
        {
            "title": "Source one",
            "url": "https://example.com/one",
            "snippet": "A grounded snippet about routing tradeoffs.",
        },
        {
            "title": "Source two",
            "url": "https://example.com/two",
            "snippet": "A grounded snippet about performance and architecture.",
        },
        {
            "title": "Source three",
            "url": "https://example.com/three",
            "snippet": "A grounded snippet about validation and system behavior.",
        },
    ]

    result = extract_facts(state)

    assert len(result["derived"]["facts"]) == 3
    assert all(fact["source_url"] for fact in result["derived"]["facts"])
    assert all(fact["source_title"] for fact in result["derived"]["facts"])
    assert any(issue["step"] == "extract_facts" for issue in result["validation"]["issues"])


def test_generate_image_prompts_falls_back_when_llm_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.steps.generate_image_prompts.get_llm_client",
        lambda: FailingLLMClient(),
    )

    state = create_initial_state("Agentic research summarizer")
    state["derived"]["styled_post"] = "A grounded technical post about evidence flow and validation."
    result = generate_image_prompts(state)

    assert len(result["derived"]["image_prompts"]) >= 2
    assert any(issue["step"] == "generate_image_prompts" for issue in result["validation"]["issues"])