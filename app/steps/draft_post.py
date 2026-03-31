from __future__ import annotations

import json

from app.clients.llm_client import LLMClientError, get_llm_client
from app.state import append_error, append_validation_issue
from app.utils.files import read_text_file


def _build_user_prompt(summary: dict) -> str:
    return json.dumps({"summary": summary}, indent=2, ensure_ascii=False)


def _fallback_draft(summary: dict) -> str:
    lines = [
        "One thing that stands out to me:",
        "",
        summary.get("context", ""),
        "",
    ]

    for insight in summary.get("insights", []):
        lines.append(f"- {insight}")

    if summary.get("implications"):
        lines.append("")
        lines.append("What matters in practice:")
        for implication in summary["implications"]:
            lines.append(f"- {implication}")

    contrarian_angle = summary.get("contrarian_angle", "").strip()
    if contrarian_angle:
        lines.append("")
        lines.append(f"A more interesting angle: {contrarian_angle}")

    return "\n".join(lines).strip()


def draft_post(state: dict) -> dict:
    summary = state["derived"]["summary"]
    if not summary:
        append_validation_issue(
            state,
            step="draft_post",
            severity="medium",
            message="No summary available for drafting.",
        )
        state["derived"]["draft"] = ""
        return state

    system_prompt = read_text_file("app/prompts/draft_post.txt")
    user_prompt = _build_user_prompt(summary)
    client = get_llm_client()

    try:
        response_text = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        state["raw"]["llm_outputs"]["draft_post"] = response_text
        state["derived"]["draft"] = response_text.strip()
    except LLMClientError as exc:
        append_error(state, f"draft_post LLM error: {exc}")
        append_validation_issue(
            state,
            step="draft_post",
            severity="medium",
            message="LLM drafting failed; using fallback draft.",
        )
        state["derived"]["draft"] = _fallback_draft(summary)

    return state