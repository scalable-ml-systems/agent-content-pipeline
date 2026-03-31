from __future__ import annotations

import json

from app.clients.llm_client import LLMClientError, get_llm_client
from app.state import append_error, append_validation_issue
from app.utils.files import read_text_file


def _build_user_prompt(facts: list[dict], styled_post: str) -> str:
    payload = {
        "facts": facts,
        "styled_post": styled_post,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def validate_style(state: dict) -> dict:
    facts = state["derived"]["facts"]
    styled_post = state["derived"]["styled_post"]

    if not styled_post:
        append_validation_issue(
            state,
            step="validate_style",
            severity="high",
            message="Styled post is empty.",
        )
        state["validation"]["style_ok"] = False
        return state

    system_prompt = read_text_file("app/prompts/validate_style.txt")
    user_prompt = _build_user_prompt(facts, styled_post)
    client = get_llm_client()

    try:
        response_text = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.0,
        )
        state["raw"]["llm_outputs"]["validate_style"] = response_text
        parsed = json.loads(response_text)
    except (LLMClientError, json.JSONDecodeError) as exc:
        append_error(state, f"validate_style error: {exc}")
        append_validation_issue(
            state,
            step="validate_style",
            severity="medium",
            message="Style validation could not be completed reliably.",
        )
        state["validation"]["style_ok"] = False
        return state

    ok = bool(parsed.get("ok", False))
    issues = parsed.get("issues", [])

    if isinstance(issues, list):
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            append_validation_issue(
                state,
                step=issue.get("step", "validate_style"),
                severity=issue.get("severity", "medium"),
                message=issue.get("message", "Unknown validation issue."),
            )

    state["validation"]["style_ok"] = ok
    return state