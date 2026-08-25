from __future__ import annotations

import httpx

from book_os_core.research_adapters import (
    CrossrefAdapter,
    OpenAlexAdapter,
    ResearchGateway,
    SemanticScholarAdapter,
    normalize_doi,
)


def test_normalize_doi_is_case_and_prefix_independent() -> None:
    assert normalize_doi(" DOI:10.1000/ABC.XYZ ") == "10.1000/abc.xyz"
    assert normalize_doi("https://doi.org/10.1000/ABC.XYZ") == "10.1000/abc.xyz"


def test_openalex_search_normalizes_metadata_without_live_http() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/works"
        assert request.url.params["search"] == "feedback loops"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "display_name": "Feedback Loops in Organizations",
                        "authorships": [{"author": {"display_name": "Ada Author"}}],
                        "publication_date": "2024-05-01",
                        "publication_year": 2024,
                        "doi": "https://doi.org/10.5555/FEEDBACK.1",
                        "primary_location": {
                            "landing_page_url": "https://example.org/work/123#abstract",
                            "source": {"display_name": "Systems Journal"},
                        },
                        "type": "article",
                        "cited_by_count": 42,
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = OpenAlexAdapter(client=client).search("feedback loops")
    assert len(result) == 1
    assert result[0].doi == "10.5555/feedback.1"
    assert result[0].authors == ["Ada Author"]
    assert result[0].container_title == "Systems Journal"
    assert result[0].citation_count == 42
    assert result[0].canonical_url == "https://example.org/work/123"


def test_crossref_search_normalizes_metadata_without_live_http() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/works"
        assert request.url.params["query.bibliographic"] == "authority systems"
        assert request.url.params["mailto"] == "book-os@example.test"
        return httpx.Response(
            200,
            json={
                "message": {
                    "items": [
                        {
                            "DOI": "10.5555/AUTHORITY.2",
                            "title": ["Authority Systems"],
                            "author": [{"given": "Bea", "family": "Researcher"}],
                            "container-title": ["Management Review"],
                            "published-online": {"date-parts": [[2023, 7, 1]]},
                            "URL": "https://doi.org/10.5555/AUTHORITY.2",
                            "type": "journal-article",
                            "is-referenced-by-count": 19,
                        }
                    ]
                }
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = CrossrefAdapter(client=client, mailto="book-os@example.test").search(
        "authority systems"
    )
    assert len(result) == 1
    assert result[0].doi == "10.5555/authority.2"
    assert result[0].authors == ["Bea Researcher"]
    assert result[0].publication_year == 2023
    assert result[0].citation_count == 19


def test_semantic_scholar_search_normalizes_metadata_without_live_http() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/graph/v1/paper/search"
        assert request.url.params["query"] == "editorial authority"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "paperId": "S2-PAPER-1",
                        "title": "Editorial Authority",
                        "authors": [{"name": "Cara Scholar"}],
                        "year": 2022,
                        "externalIds": {"DOI": "10.5555/EDITORIAL.3", "CorpusId": 123},
                        "url": "https://www.semanticscholar.org/paper/S2-PAPER-1",
                        "venue": "Editing Studies",
                        "publicationTypes": ["JournalArticle"],
                        "publicationDate": "2022-01-01",
                        "abstract": "A provider-supplied abstract.",
                        "citationCount": 7,
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = SemanticScholarAdapter(client=client).search("editorial authority")
    assert len(result) == 1
    assert result[0].doi == "10.5555/editorial.3"
    assert result[0].abstract == "A provider-supplied abstract."
    assert result[0].raw_identifiers["corpusid"] == "123"


def test_gateway_queries_selected_mocked_adapters_only() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        if request.url.host == "api.openalex.org":
            return httpx.Response(200, json={"results": []})
        if request.url.host == "api.crossref.org":
            return httpx.Response(200, json={"message": {"items": []}})
        raise AssertionError(f"unexpected host {request.url.host}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gateway = ResearchGateway(
        {
            "openalex": OpenAlexAdapter(client=client),
            "crossref": CrossrefAdapter(client=client),
        }
    )
    assert gateway.search("bounded query", providers=["openalex", "crossref"]) == []
    assert calls == ["api.openalex.org", "api.crossref.org"]
