from __future__ import annotations

import json

from app.clients.llm_client import LLMClientError, get_llm_client
from app.state import append_error, append_validation_issue
from app.utils.files import read_text_file


def _build_user_prompt(topic: str, styled_post: str) -> str:
    payload = {
        "topic": topic,
        "styled_post": styled_post,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _fallback_image_prompts(topic: str) -> list[str]:
    return [
        (
            f"Minimal high-contrast system diagram representing {topic}, "
            "layered pipeline, evidence flow between stages, clean geometric layout, no text"
        ),
        (
            f"Professional editorial illustration for {topic}, "
            "structured boxes and arrows, grounded technical workflow, dark neutral background, no text"
        ),
        (
            f"Abstract architecture visual for {topic}, "
            "signals moving through validation gates and transformation layers, minimalist style, no text"
        ),
    ]


def generate_image_prompts(state: dict) -> dict:
    topic = state["topic"]
    styled_post = state["derived"]["styled_post"]

    if not styled_post:
        append_validation_issue(
            state,
            step="generate_image_prompts",
            severity="medium",
            message="No styled post available; using fallback image prompts.",
        )
        state["derived"]["image_prompts"] = _fallback_image_prompts(topic)
        return state

    system_prompt = read_text_file("app/prompts/generate_image_prompts.txt")
    user_prompt = _build_user_prompt(topic, styled_post)
    client = get_llm_client()

    try:
        response_text = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        state["raw"]["llm_outputs"]["generate_image_prompts"] = response_text
    except LLMClientError as exc:
        append_error(state, f"generate_image_prompts LLM error: {exc}")
        append_validation_issue(
            state,
            step="generate_image_prompts",
            severity="medium",
            message="Image prompt generation failed; using fallback prompts.",
        )
        state["derived"]["image_prompts"] = _fallback_image_prompts(topic)
        return state

    try:
        parsed = json.loads(response_text)
        if not isinstance(parsed, list):
            raise ValueError("Expected a top-level JSON list.")
        prompts = [item.strip() for item in parsed if isinstance(item, str) and item.strip()]
        if len(prompts) < 2:
            raise ValueError("Expected at least 2 usable image prompts.")
        state["derived"]["image_prompts"] = prompts[:4]
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        append_error(state, f"generate_image_prompts parse error: {exc}")
        append_validation_issue(
            state,
            step="generate_image_prompts",
            severity="low",
            message="Could not parse image prompt output; using fallback prompts.",
        )
        state["derived"]["image_prompts"] = _fallback_image_prompts(topic)

    return state