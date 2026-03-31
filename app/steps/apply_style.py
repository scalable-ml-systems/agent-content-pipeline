from __future__ import annotations

import json

from app.clients.llm_client import LLMClientError, get_llm_client
from app.state import append_error, append_validation_issue
from app.utils.files import read_text_file
from app.utils.template_loader import load_yaml_template


def _build_user_prompt(draft: str, template: dict) -> str:
    payload = {
        "draft": draft,
        "style_template": template,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def apply_style(state: dict) -> dict:
    draft = state["derived"]["draft"]
    if not draft:
        append_validation_issue(
            state,
            step="apply_style",
            severity="medium",
            message="No draft available for style application.",
        )
        state["derived"]["styled_post"] = ""
        return state

    system_prompt = read_text_file("app/prompts/apply_style.txt")
    style_template = load_yaml_template("app/templates/linkedin_style.yaml")
    user_prompt = _build_user_prompt(draft, style_template)
    client = get_llm_client()

    try:
        response_text = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        state["raw"]["llm_outputs"]["apply_style"] = response_text
        state["derived"]["styled_post"] = response_text.strip()
    except LLMClientError as exc:
        append_error(state, f"apply_style LLM error: {exc}")
        append_validation_issue(
            state,
            step="apply_style",
            severity="medium",
            message="Style rewrite failed; using original draft.",
        )
        state["derived"]["styled_post"] = draft

    return state