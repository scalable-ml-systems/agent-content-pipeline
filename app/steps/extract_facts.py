from __future__ import annotations

import json

from app.clients.llm_client import LLMClientError, get_llm_client
from app.models import Fact
from app.state import append_error, append_validation_issue
from app.utils.files import read_text_file


def _build_user_prompt(search_results: list[dict]) -> str:
    lines: list[str] = []
    for idx, item in enumerate(search_results, start=1):
        lines.append(f"[SOURCE {idx}]")
        lines.append(f"TITLE: {item['title']}")
        lines.append(f"URL: {item['url']}")
        lines.append(f"SNIPPET: {item['snippet']}")
        lines.append("")
    return "\n".join(lines).strip()


def _fallback_extract(search_results: list[dict]) -> list[dict]:
    facts: list[dict] = []
    for item in search_results:
        facts.append(
            Fact(
                fact=f"{item['title']} presents a relevant claim or perspective related to the topic.",
                source_url=item["url"],
                source_title=item["title"],
                fact_type="claim",
                evidence_snippet=item["snippet"],
                confidence="medium",
            ).model_dump(mode="json")
        )
    return facts


def extract_facts(state: dict) -> dict:
    search_results = state["raw"]["search_results"]
    if not search_results:
        append_validation_issue(
            state,
            step="extract_facts",
            severity="medium",
            message="No search results available for fact extraction.",
        )
        state["derived"]["facts"] = []
        return state

    system_prompt = read_text_file("app/prompts/extract_facts.txt")
    user_prompt = _build_user_prompt(search_results)
    client = get_llm_client()

    try:
        response_text = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
        )
        state["raw"]["llm_outputs"]["extract_facts"] = response_text
    except LLMClientError as exc:
        append_error(state, f"extract_facts LLM error: {exc}")
        append_validation_issue(
            state,
            step="extract_facts",
            severity="medium",
            message="LLM extraction failed; using fallback fact extraction.",
        )
        state["derived"]["facts"] = _fallback_extract(search_results)
        return state

    try:
        parsed = json.loads(response_text)
        if not isinstance(parsed, list):
            raise ValueError("Expected a top-level JSON list of facts.")

        facts = [Fact(**item).model_dump(mode="json") for item in parsed]
        state["derived"]["facts"] = facts
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        append_error(state, f"extract_facts parse error: {exc}")
        append_validation_issue(
            state,
            step="extract_facts",
            severity="low",
            message="Could not parse LLM fact output; using fallback fact extraction.",
        )
        state["derived"]["facts"] = _fallback_extract(search_results)

    return state