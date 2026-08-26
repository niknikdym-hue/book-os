from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Protocol

import httpx

from .secrets import SecretStore


class EmbeddingError(RuntimeError):
    pass


class EmbeddingProviderError(EmbeddingError):
    pass


class EmbeddingOutputError(EmbeddingError):
    pass


@dataclass(frozen=True)
class EmbeddingBatchResult:
    provider: str
    model: str
    model_version: str
    vectors: list[list[float]]
    usage: dict[str, Any]


class EmbeddingAdapter(Protocol):
    provider_name: str

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult: ...


def embedding_config_hash(provider: str, model: str, model_version: str, dimension: int) -> str:
    payload = json.dumps(
        {
            "provider": provider,
            "model": model,
            "model_version": model_version,
            "dimension": dimension,
            "normalization": "cosine-v1",
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EmbeddingGateway:
    def __init__(self, adapters: dict[str, EmbeddingAdapter]):
        self._adapters = dict(adapters)

    def embed(self, texts: list[str], *, provider: str, model: str) -> EmbeddingBatchResult:
        if not texts:
            raise EmbeddingOutputError("embedding request must contain at least one text")
        try:
            adapter = self._adapters[provider]
        except KeyError as exc:
            raise EmbeddingProviderError(
                f"embedding provider is not configured: {provider}"
            ) from exc
        result = adapter.embed(texts, model)
        if len(result.vectors) != len(texts):
            raise EmbeddingOutputError("embedding provider returned the wrong number of vectors")
        dimension: int | None = None
        for vector in result.vectors:
            if not vector:
                raise EmbeddingOutputError("embedding vector must not be empty")
            if dimension is None:
                dimension = len(vector)
            elif len(vector) != dimension:
                raise EmbeddingOutputError("embedding vectors must have one consistent dimension")
            if not all(math.isfinite(float(value)) for value in vector):
                raise EmbeddingOutputError("embedding vector contains a non-finite value")
        return result


class DeterministicFakeEmbeddingAdapter:
    provider_name = "fake"

    def __init__(
        self,
        *,
        mapping: dict[str, list[float]] | None = None,
        dimension: int = 8,
        fail: bool = False,
        model_version: str = "fake-v1",
    ) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.mapping = dict(mapping or {})
        self.dimension = dimension
        self.fail = fail
        self.model_version = model_version
        self.calls: list[tuple[list[str], str]] = []

    def _derived(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(self.dimension):
            byte = digest[index % len(digest)]
            values.append((float(byte) - 127.5) / 127.5)
        return values

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult:
        self.calls.append((list(texts), model))
        if self.fail:
            raise EmbeddingProviderError("deterministic fake embedding failure")
        vectors = [list(self.mapping.get(text, self._derived(text))) for text in texts]
        return EmbeddingBatchResult(
            provider=self.provider_name,
            model=model,
            model_version=self.model_version,
            vectors=vectors,
            usage={"input_count": len(texts)},
        )


class OpenAIEmbeddingAdapter:
    provider_name = "openai"

    def __init__(
        self,
        secret_store: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://api.openai.com/v1/embeddings",
        timeout_seconds: float = 60.0,
    ) -> None:
        self._secret_store = secret_store
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult:
        api_key = self._secret_store.get_secret("openai_api_key")
        try:
            response = self._client.post(
                self._endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "input": texts, "encoding_format": "float"},
                timeout=self._timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError("OpenAI embeddings request failed") from exc
        if response.status_code >= 400:
            raise EmbeddingProviderError(f"OpenAI embeddings HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise EmbeddingOutputError("OpenAI embeddings response must be an object")
        raw_data = payload.get("data")
        if not isinstance(raw_data, list):
            raise EmbeddingOutputError("OpenAI embeddings response has no data array")
        ordered: list[tuple[int, list[float]]] = []
        for item in raw_data:
            if not isinstance(item, dict):
                raise EmbeddingOutputError("OpenAI embedding item must be an object")
            index = item.get("index")
            raw_vector = item.get("embedding")
            if not isinstance(index, int) or not isinstance(raw_vector, list):
                raise EmbeddingOutputError("OpenAI embedding item is malformed")
            try:
                vector = [float(value) for value in raw_vector]
            except (TypeError, ValueError) as exc:
                raise EmbeddingOutputError("OpenAI embedding contains a non-numeric value") from exc
            ordered.append((index, vector))
        ordered.sort(key=lambda pair: pair[0])
        usage = payload.get("usage")
        model_version = payload.get("model")
        return EmbeddingBatchResult(
            provider=self.provider_name,
            model=model,
            model_version=str(model_version) if model_version else model,
            vectors=[vector for _, vector in ordered],
            usage=usage if isinstance(usage, dict) else {},
        )
