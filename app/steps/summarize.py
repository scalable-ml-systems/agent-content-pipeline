from __future__ import annotations

import json

from app.clients.llm_client import LLMClientError, get_llm_client
from app.models import Summary
from app.state import append_error, append_validation_issue
from app.utils.files import read_text_file


def _build_user_prompt(facts: list[dict]) -> str:
    payload = {"facts": facts}
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _fallback_summary(facts: list[dict]) -> dict:
    insights = [fact["fact"] for fact in facts[:3]]
    return Summary(
        context="This topic matters because it affects how teams build credible, production-oriented systems.",
        insights=insights,
        implications=[
            "Grounding and validation directly affect output quality.",
            "System design matters as much as generation quality.",
        ],
        contrarian_angle="The bottleneck is often not generation itself, but how evidence is transformed and preserved.",
    ).model_dump()


def summarize(state: dict) -> dict:
    facts = state["derived"]["facts"]
    if not facts:
        append_validation_issue(
            state,
            step="summarize",
            severity="medium",
            message="No facts available for summarization.",
        )
        state["derived"]["summary"] = Summary().model_dump()
        return state

    system_prompt = read_text_file("app/prompts/summarize.txt")
    user_prompt = _build_user_prompt(facts)
    client = get_llm_client()

    try:
        response_text = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
        )
        state["raw"]["llm_outputs"]["summarize"] = response_text
    except LLMClientError as exc:
        append_error(state, f"summarize LLM error: {exc}")
        append_validation_issue(
            state,
            step="summarize",
            severity="medium",
            message="LLM summarization failed; using fallback summary.",
        )
        state["derived"]["summary"] = _fallback_summary(facts)
        return state

    try:
        parsed = json.loads(response_text)
        summary = Summary(**parsed)
        state["derived"]["summary"] = summary.model_dump()
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        append_error(state, f"summarize parse error: {exc}")
        append_validation_issue(
            state,
            step="summarize",
            severity="low",
            message="Could not parse summary output; using fallback summary.",
        )
        state["derived"]["summary"] = _fallback_summary(facts)

    return state