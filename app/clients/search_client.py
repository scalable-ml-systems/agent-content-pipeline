from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Protocol, Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from app.models import SearchResult


class SearchClientError(RuntimeError):
    """Raised when the search client cannot complete a request."""


class SearchClient(Protocol):
    """Contract for all search client implementations."""

    def search(self, topic: str, top_k: int) -> list[SearchResult]:
        """Return normalized search results for a topic."""
        ...


@dataclass(frozen=True)
class MockSearchClient:
    """Deterministic local fallback used when no provider is configured."""

    def search(self, topic: str, top_k: int) -> list[SearchResult]:
        safe_top_k = max(1, top_k)

        base_results = [
            SearchResult(
                title=f"{topic}: overview and practical implications",
                url="https://example.com/overview",
                snippet=f"Overview source for {topic}, including practical implications and tradeoffs.",
            ),
            SearchResult(
                title=f"{topic}: architecture patterns",
                url="https://example.com/architecture",
                snippet=f"Architecture patterns and implementation concerns for {topic}.",
            ),
            SearchResult(
                title=f"{topic}: engineering tradeoffs",
                url="https://example.com/tradeoffs",
                snippet=f"Tradeoffs, constraints, and operational considerations for {topic}.",
            ),
            SearchResult(
                title=f"{topic}: production reliability concerns",
                url="https://example.com/reliability",
                snippet=f"Reliability, validation, and quality concerns for {topic}.",
            ),
            SearchResult(
                title=f"{topic}: performance and evaluation",
                url="https://example.com/evaluation",
                snippet=f"Performance and evaluation considerations for {topic}.",
            ),
        ]
        return base_results[:safe_top_k]


@dataclass(frozen=True)
class TavilySearchClient:
    """
    Thin HTTP client for a real search provider.

    For Phase 1, this is intentionally small:
    - one method
    - normalized output
    - explicit failure handling
    """

    api_key: str
    base_url: str = "https://api.tavily.com/search"
    timeout_seconds: int = 20

    def search(self, topic: str, top_k: int) -> list[SearchResult]:
        if requests is None:
            raise SearchClientError(
                "requests is not installed. Add it to dependencies before using TavilySearchClient."
            )

        payload: dict[str, Any] = {
            "api_key": self.api_key,
            "query": topic,
            "max_results": top_k,
            "search_depth": "basic",
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except Exception as exc:
            raise SearchClientError(f"Search provider request failed: {exc}") from exc

        data = response.json()
        raw_results = data.get("results", [])

        normalized: list[SearchResult] = []
        for item in raw_results:
            url = item.get("url")
            title = item.get("title")
            content = item.get("content")

            if not url or not title or not content:
                continue

            normalized.append(
                SearchResult(
                    title=title.strip(),
                    url=url,
                    snippet=content.strip(),
                )
            )

        if not normalized:
            raise SearchClientError("Search provider returned no usable results.")

        return normalized


def get_search_client() -> SearchClient:
    """
    Factory for selecting a search client.

    Phase 1 behavior:
    - use Tavily if TAVILY_API_KEY exists
    - otherwise use mock client so local development is never blocked
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if api_key:
        return TavilySearchClient(api_key=api_key)

    return MockSearchClient()