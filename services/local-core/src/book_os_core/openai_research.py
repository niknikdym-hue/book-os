from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlsplit

import httpx

from .research_adapters import (
    ResearchAdapter,
    ResearchCandidate,
    ResearchGateway,
    ResearchProviderError,
    normalize_url,
)
from .secrets import SecretNotFound, SecretStore


class OpenAIWebSearchAdapter:
    """Bounded web discovery for BOOK OS Research Engine.

    The adapter imports only source identities returned by the hosted web-search tool.
    Model prose is deliberately ignored and can never become Evidence by itself.
    """

    provider_name = "openai_web"

    def __init__(
        self,
        secret_store: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://api.openai.com/v1/responses",
        model: str = "gpt-5.6-luna",
        timeout_seconds: float = 60.0,
    ) -> None:
        self._secret_store = secret_store
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._endpoint = endpoint
        self._model = model
        self._timeout_seconds = timeout_seconds

    def _body(self, query: str) -> dict[str, object]:
        return {
            "model": self._model,
            "store": False,
            "input": [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Use exactly one public-web search to discover relevant, preferably "
                                "primary or authoritative sources for the research query. BOOK OS will "
                                "use only the returned source identities; do not invent URLs."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": query}],
                },
            ],
            "tools": [{"type": "web_search", "search_context_size": "low"}],
            "tool_choice": "required",
            "include": ["web_search_call.action.sources"],
            "max_tool_calls": 1,
            "max_output_tokens": 128,
            "reasoning": {"effort": "none"},
        }

    @staticmethod
    def _source_rows(payload: dict[str, object]) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        output = payload.get("output")
        if not isinstance(output, list):
            return rows
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "web_search_call":
                action = item.get("action")
                if isinstance(action, dict):
                    sources = action.get("sources")
                    if isinstance(sources, list):
                        rows.extend(source for source in sources if isinstance(source, dict))
            if item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                annotations = part.get("annotations")
                if not isinstance(annotations, list):
                    continue
                for annotation in annotations:
                    if isinstance(annotation, dict) and annotation.get("type") == "url_citation":
                        rows.append(annotation)
        return rows

    @staticmethod
    def _candidate(source: dict[str, object], response_id: str | None) -> ResearchCandidate | None:
        raw_url = source.get("url")
        if not isinstance(raw_url, str):
            return None
        try:
            canonical_url = normalize_url(raw_url)
            if not canonical_url or not canonical_url.startswith(("http://", "https://")):
                return None
            host = urlsplit(canonical_url).hostname
        except ValueError:
            return None
        raw_title = source.get("title")
        title = raw_title.strip() if isinstance(raw_title, str) and raw_title.strip() else None
        if title is None:
            title = host or canonical_url
        raw_ids = {"openai_web": canonical_url}
        if response_id:
            raw_ids["openai_response"] = response_id
        return ResearchCandidate(
            provider=OpenAIWebSearchAdapter.provider_name,
            external_id=canonical_url,
            title=title,
            organization=host,
            canonical_url=canonical_url,
            source_type="web-page",
            provider_url=canonical_url,
            raw_identifiers=raw_ids,
        )

    def search(self, query: str, *, limit: int = 5) -> list[ResearchCandidate]:
        query = query.strip()
        if not query:
            raise ValueError("research query must not be blank")
        api_key = self._secret_store.get_secret("openai_api_key")
        try:
            response = self._client.post(
                self._endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=self._body(query),
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ResearchProviderError(f"{self.provider_name} search failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise ResearchProviderError(f"{self.provider_name} returned a non-object response")

        response_id = payload.get("id") if isinstance(payload.get("id"), str) else None
        candidates: list[ResearchCandidate] = []
        seen: set[str] = set()
        for source in self._source_rows(payload):
            candidate = self._candidate(source, response_id)
            if candidate is None or candidate.external_id in seen:
                continue
            seen.add(candidate.external_id)
            candidates.append(candidate)
            if len(candidates) >= max(1, min(limit, 10)):
                break
        return candidates


class ProductionResearchGateway(ResearchGateway):
    """Native BOOK OS research composition with fail-soft optional web enrichment.

    The scholarly trio remains the canonical baseline. Its normal desktop search is enriched with
    OpenAI web discovery when that optional adapter is configured and available. A missing OpenAI
    credential or transient web-search failure never discards already discovered scholarly results.
    Explicit narrower provider selections remain narrow and keep their ordinary failure semantics.
    """

    _DEFAULT_SCHOLARLY = ("openalex", "crossref", "semantic_scholar")

    def __init__(self, adapters: Mapping[str, ResearchAdapter]) -> None:
        super().__init__(adapters)

    def search(
        self,
        query: str,
        *,
        providers: list[str] | None = None,
        limit_per_provider: int = 5,
    ) -> list[ResearchCandidate]:
        selected = list(self._DEFAULT_SCHOLARLY) if not providers else list(providers)
        enrich_with_web = selected == list(self._DEFAULT_SCHOLARLY)
        results = super().search(
            query,
            providers=selected,
            limit_per_provider=limit_per_provider,
        )

        web_adapter = self.adapters.get("openai_web") if enrich_with_web else None
        if web_adapter is None:
            return results
        try:
            results.extend(web_adapter.search(query, limit=limit_per_provider))
        except (SecretNotFound, ResearchProviderError):
            pass
        return results
