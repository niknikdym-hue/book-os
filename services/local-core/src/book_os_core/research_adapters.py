from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import BaseModel, Field, field_validator


class ResearchProviderError(RuntimeError):
    pass


class ResearchCandidate(BaseModel):
    provider: str
    external_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    organization: str | None = None
    publication_date: str | None = None
    publication_year: int | None = None
    doi: str | None = None
    canonical_url: str | None = None
    container_title: str | None = None
    source_type: str = "scholarly-work"
    abstract: str | None = None
    citation_count: int | None = None
    provider_url: str | None = None
    raw_identifiers: dict[str, str] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def nonblank_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("candidate title must not be blank")
        return value


class ResearchAdapter(Protocol):
    provider_name: str

    def search(self, query: str, *, limit: int = 5) -> list[ResearchCandidate]: ...


def normalize_doi(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "http://dx.doi.org/", "doi:"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    normalized = normalized.strip()
    return normalized or None


def normalize_url(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return value
    path = parts.path.rstrip("/") or ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _year(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


class _HttpAdapter:
    provider_name = "base"

    def __init__(self, *, client: httpx.Client | None = None, timeout: float = 20.0) -> None:
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._timeout = timeout

    def _get(
        self,
        url: str,
        *,
        params: Mapping[str, str | int | float | bool | None],
    ) -> dict[str, Any]:
        try:
            response = self._client.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ResearchProviderError(f"{self.provider_name} search failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise ResearchProviderError(f"{self.provider_name} returned a non-object response")
        return payload


class OpenAlexAdapter(_HttpAdapter):
    provider_name = "openalex"
    endpoint = "https://api.openalex.org/works"

    def search(self, query: str, *, limit: int = 5) -> list[ResearchCandidate]:
        payload = self._get(
            self.endpoint, params={"search": query, "per-page": max(1, min(limit, 25))}
        )
        rows = payload.get("results")
        if not isinstance(rows, list):
            return []
        candidates: list[ResearchCandidate] = []
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            external_id = _text(raw.get("id"))
            title = _text(raw.get("display_name")) or _text(raw.get("title"))
            if not external_id or not title:
                continue
            authors: list[str] = []
            authorships = raw.get("authorships")
            if isinstance(authorships, list):
                for authorship in authorships:
                    if isinstance(authorship, dict):
                        author = authorship.get("author")
                        if isinstance(author, dict):
                            name = _text(author.get("display_name"))
                            if name:
                                authors.append(name)
            primary_location = raw.get("primary_location")
            container: str | None = None
            landing: str | None = None
            if isinstance(primary_location, dict):
                landing = _text(primary_location.get("landing_page_url"))
                source = primary_location.get("source")
                if isinstance(source, dict):
                    container = _text(source.get("display_name"))
            doi = normalize_doi(_text(raw.get("doi")))
            candidates.append(
                ResearchCandidate(
                    provider=self.provider_name,
                    external_id=external_id,
                    title=title,
                    authors=authors,
                    publication_date=_text(raw.get("publication_date")),
                    publication_year=_year(raw.get("publication_year")),
                    doi=doi,
                    canonical_url=normalize_url(
                        landing or (f"https://doi.org/{doi}" if doi else external_id)
                    ),
                    container_title=container,
                    source_type=_text(raw.get("type")) or "scholarly-work",
                    citation_count=_year(raw.get("cited_by_count")),
                    provider_url=external_id,
                    raw_identifiers={"openalex": external_id},
                )
            )
        return candidates


class CrossrefAdapter(_HttpAdapter):
    provider_name = "crossref"
    endpoint = "https://api.crossref.org/works"

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout: float = 20.0,
        mailto: str | None = None,
    ) -> None:
        super().__init__(client=client, timeout=timeout)
        self.mailto = mailto

    def search(self, query: str, *, limit: int = 5) -> list[ResearchCandidate]:
        params: dict[str, object] = {
            "query.bibliographic": query,
            "rows": max(1, min(limit, 25)),
        }
        if self.mailto:
            params["mailto"] = self.mailto
        payload = self._get(self.endpoint, params=params)
        message = payload.get("message")
        rows = message.get("items") if isinstance(message, dict) else None
        if not isinstance(rows, list):
            return []
        candidates: list[ResearchCandidate] = []
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            doi = normalize_doi(_text(raw.get("DOI")))
            external_id = doi or _text(raw.get("URL"))
            title_value = raw.get("title")
            title = _text(title_value[0]) if isinstance(title_value, list) and title_value else None
            if not external_id or not title:
                continue
            authors: list[str] = []
            author_rows = raw.get("author")
            if isinstance(author_rows, list):
                for author in author_rows:
                    if not isinstance(author, dict):
                        continue
                    given = _text(author.get("given")) or ""
                    family = _text(author.get("family")) or ""
                    name = f"{given} {family}".strip()
                    if name:
                        authors.append(name)
            container_value = raw.get("container-title")
            container = (
                _text(container_value[0])
                if isinstance(container_value, list) and container_value
                else None
            )
            date_value = (
                raw.get("published-print") or raw.get("published-online") or raw.get("issued")
            )
            year: int | None = None
            if isinstance(date_value, dict):
                parts = date_value.get("date-parts")
                if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
                    year = _year(parts[0][0])
            candidates.append(
                ResearchCandidate(
                    provider=self.provider_name,
                    external_id=external_id,
                    title=title,
                    authors=authors,
                    publication_year=year,
                    doi=doi,
                    canonical_url=normalize_url(
                        _text(raw.get("URL")) or (f"https://doi.org/{doi}" if doi else None)
                    ),
                    container_title=container,
                    source_type=_text(raw.get("type")) or "scholarly-work",
                    citation_count=_year(raw.get("is-referenced-by-count")),
                    provider_url=normalize_url(_text(raw.get("URL"))),
                    raw_identifiers={"crossref": external_id},
                )
            )
        return candidates


class SemanticScholarAdapter(_HttpAdapter):
    provider_name = "semantic_scholar"
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout: float = 20.0,
        api_key: str | None = None,
    ) -> None:
        headers = {"x-api-key": api_key} if api_key else None
        owned_client = client or httpx.Client(
            timeout=timeout, follow_redirects=True, headers=headers
        )
        super().__init__(client=owned_client, timeout=timeout)

    def search(self, query: str, *, limit: int = 5) -> list[ResearchCandidate]:
        fields = (
            "paperId,title,authors,year,externalIds,url,venue,publicationTypes,"
            "publicationDate,abstract,citationCount"
        )
        payload = self._get(
            self.endpoint,
            params={"query": query, "limit": max(1, min(limit, 25)), "fields": fields},
        )
        rows = payload.get("data")
        if not isinstance(rows, list):
            return []
        candidates: list[ResearchCandidate] = []
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            external_id = _text(raw.get("paperId"))
            title = _text(raw.get("title"))
            if not external_id or not title:
                continue
            authors: list[str] = []
            author_rows = raw.get("authors")
            if isinstance(author_rows, list):
                for author in author_rows:
                    if isinstance(author, dict):
                        name = _text(author.get("name"))
                        if name:
                            authors.append(name)
            external_ids = raw.get("externalIds")
            doi: str | None = None
            raw_ids = {"semantic_scholar": external_id}
            if isinstance(external_ids, dict):
                doi = normalize_doi(_text(external_ids.get("DOI")))
                for key, value in external_ids.items():
                    if isinstance(key, str) and isinstance(value, (str, int)):
                        raw_ids[key.lower()] = str(value)
            publication_types = raw.get("publicationTypes")
            source_type = (
                str(publication_types[0])
                if isinstance(publication_types, list) and publication_types
                else "scholarly-work"
            )
            candidates.append(
                ResearchCandidate(
                    provider=self.provider_name,
                    external_id=external_id,
                    title=title,
                    authors=authors,
                    publication_date=_text(raw.get("publicationDate")),
                    publication_year=_year(raw.get("year")),
                    doi=doi,
                    canonical_url=normalize_url(
                        _text(raw.get("url")) or (f"https://doi.org/{doi}" if doi else None)
                    ),
                    container_title=_text(raw.get("venue")),
                    source_type=source_type,
                    abstract=_text(raw.get("abstract")),
                    citation_count=_year(raw.get("citationCount")),
                    provider_url=normalize_url(_text(raw.get("url"))),
                    raw_identifiers=raw_ids,
                )
            )
        return candidates


class ResearchGateway:
    def __init__(self, adapters: Mapping[str, ResearchAdapter]) -> None:
        self.adapters = dict(adapters)

    def search(
        self,
        query: str,
        *,
        providers: list[str] | None = None,
        limit_per_provider: int = 5,
    ) -> list[ResearchCandidate]:
        query = query.strip()
        if not query:
            raise ValueError("research query must not be blank")
        selected = providers or list(self.adapters)
        results: list[ResearchCandidate] = []
        for provider in selected:
            adapter = self.adapters.get(provider)
            if adapter is None:
                raise ResearchProviderError(f"research provider is not configured: {provider}")
            results.extend(adapter.search(query, limit=limit_per_provider))
        return results
