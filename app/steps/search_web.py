from __future__ import annotations

from app.clients.search_client import SearchClientError, get_search_client
from app.config import get_settings
from app.state import append_error, append_validation_issue


def search_web(state: dict) -> dict:
    topic = state["topic"]
    settings = get_settings()
    client = get_search_client()

    try:
        results = client.search(topic=topic, top_k=settings.search_top_k)
    except SearchClientError as exc:
        append_error(state, f"search_web provider error: {exc}")
        append_validation_issue(
            state,
            step="search_web",
            severity="medium",
            message="Search provider failed; continuing with empty result set.",
        )
        state["raw"]["search_results"] = []
        state["sources"] = []
        return state

    serialized = [item.model_dump(mode="json") for item in results]
    state["raw"]["search_results"] = serialized
    state["sources"] = [item["url"] for item in serialized]

    if len(serialized) < settings.search_top_k:
        append_validation_issue(
            state,
            step="search_web",
            severity="low",
            message=(
                f"Search returned {len(serialized)} results, below target "
                f"of {settings.search_top_k}."
            ),
        )

    return state