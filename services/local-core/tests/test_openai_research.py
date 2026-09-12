from __future__ import annotations

import json

import httpx

from book_os_core.openai_research import OpenAIWebSearchAdapter, ProductionResearchGateway
from book_os_core.research_adapters import ResearchCandidate, ResearchProviderError
from book_os_core.secrets import DictSecretStore


class _FakeAdapter:
    def __init__(
        self,
        provider_name: str,
        calls: list[str],
        *,
        results: list[ResearchCandidate] | None = None,
        fail: bool = False,
    ) -> None:
        self.provider_name = provider_name
        self._calls = calls
        self._results = results or []
        self._fail = fail

    def search(self, query: str, *, limit: int = 5) -> list[ResearchCandidate]:
        self._calls.append(self.provider_name)
        if self._fail:
            raise ResearchProviderError(f"{self.provider_name} unavailable")
        return list(self._results)


def _scholarly_candidate() -> ResearchCandidate:
    return ResearchCandidate(
        provider="openalex",
        external_id="openalex:fixture",
        title="Rights-clean scholarly result",
        canonical_url="https://example.org/scholarly",
        source_type="journal-article",
    )


def test_openai_web_search_is_bounded_and_imports_only_real_source_rows() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("Authorization")
        body = json.loads(request.content)
        captured["body"] = body
        return httpx.Response(
            200,
            json={
                "id": "resp_web_fixture",
                "output": [
                    {
                        "type": "web_search_call",
                        "id": "ws_fixture",
                        "status": "completed",
                        "action": {
                            "type": "search",
                            "sources": [
                                {
                                    "type": "url",
                                    "url": "https://example.org/report#section",
                                    "title": "Primary Report",
                                },
                                {
                                    "type": "url",
                                    "url": "https://example.net/data/",
                                    "title": "Official Data",
                                },
                            ],
                        },
                    },
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Model prose that BOOK OS must not treat as evidence.",
                                "annotations": [
                                    {
                                        "type": "url_citation",
                                        "url": "https://example.org/report#section",
                                        "title": "Primary Report",
                                    }
                                ],
                            }
                        ],
                    },
                ],
            },
        )

    adapter = OpenAIWebSearchAdapter(
        DictSecretStore({"openai_api_key": "web-search-secret"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test/v1/responses",
    )
    result = adapter.search("current primary sources", limit=5)

    assert captured["authorization"] == "Bearer web-search-secret"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["model"] == "gpt-5.6-luna"
    assert body["store"] is False
    assert body["tools"] == [{"type": "web_search", "search_context_size": "low"}]
    assert body["tool_choice"] == "required"
    assert body["max_tool_calls"] == 1
    assert body["max_output_tokens"] == 128
    assert body["reasoning"] == {"effort": "none"}
    assert body["include"] == ["web_search_call.action.sources"]
    assert "web-search-secret" not in json.dumps(body)

    assert [candidate.canonical_url for candidate in result] == [
        "https://example.org/report",
        "https://example.net/data",
    ]
    assert result[0].title == "Primary Report"
    assert result[0].organization == "example.org"
    assert result[0].provider == "openai_web"
    assert result[0].source_type == "web-page"
    assert result[0].abstract is None
    assert result[0].raw_identifiers["openai_response"] == "resp_web_fixture"


def test_malformed_web_source_rows_are_skipped_without_losing_valid_sources() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "resp_malformed_fixture",
                "output": [
                    {
                        "type": "web_search_call",
                        "action": {
                            "sources": [
                                {"url": "http://[bad", "title": "Malformed"},
                                {"url": "https://example.org/good", "title": "Valid"},
                            ]
                        },
                    }
                ],
            },
        )

    adapter = OpenAIWebSearchAdapter(
        DictSecretStore({"openai_api_key": "web-search-secret"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test/v1/responses",
    )

    result = adapter.search("mixed source rows")

    assert [candidate.canonical_url for candidate in result] == ["https://example.org/good"]


def test_production_gateway_enriches_only_the_default_scholarly_search() -> None:
    calls: list[str] = []
    gateway = ProductionResearchGateway(
        {
            "openalex": _FakeAdapter("openalex", calls),
            "crossref": _FakeAdapter("crossref", calls),
            "semantic_scholar": _FakeAdapter("semantic_scholar", calls),
            "openai_web": _FakeAdapter("openai_web", calls),
        }
    )

    gateway.search(
        "default research",
        providers=["openalex", "crossref", "semantic_scholar"],
    )
    assert calls == ["openalex", "crossref", "semantic_scholar", "openai_web"]

    calls.clear()
    gateway.search("scholarly only", providers=["openalex"])
    assert calls == ["openalex"]


def test_empty_provider_list_uses_fail_soft_default_scholarly_path() -> None:
    calls: list[str] = []
    scholarly = _scholarly_candidate()
    gateway = ProductionResearchGateway(
        {
            "openalex": _FakeAdapter("openalex", calls, results=[scholarly]),
            "crossref": _FakeAdapter("crossref", calls),
            "semantic_scholar": _FakeAdapter("semantic_scholar", calls),
            "openai_web": _FakeAdapter("openai_web", calls, fail=True),
        }
    )

    results = gateway.search("default research", providers=[])

    assert calls == ["openalex", "crossref", "semantic_scholar", "openai_web"]
    assert results == [scholarly]


def test_optional_web_failure_never_discards_scholarly_results() -> None:
    calls: list[str] = []
    scholarly = _scholarly_candidate()
    gateway = ProductionResearchGateway(
        {
            "openalex": _FakeAdapter("openalex", calls, results=[scholarly]),
            "crossref": _FakeAdapter("crossref", calls),
            "semantic_scholar": _FakeAdapter("semantic_scholar", calls),
            "openai_web": _FakeAdapter("openai_web", calls, fail=True),
        }
    )

    results = gateway.search("default research")

    assert calls == ["openalex", "crossref", "semantic_scholar", "openai_web"]
    assert results == [scholarly]


def test_missing_openai_key_never_breaks_default_scholarly_search() -> None:
    calls: list[str] = []
    scholarly = _scholarly_candidate()
    gateway = ProductionResearchGateway(
        {
            "openalex": _FakeAdapter("openalex", calls, results=[scholarly]),
            "crossref": _FakeAdapter("crossref", calls),
            "semantic_scholar": _FakeAdapter("semantic_scholar", calls),
            "openai_web": OpenAIWebSearchAdapter(DictSecretStore({})),
        }
    )

    results = gateway.search("default research")

    assert calls == ["openalex", "crossref", "semantic_scholar"]
    assert results == [scholarly]
