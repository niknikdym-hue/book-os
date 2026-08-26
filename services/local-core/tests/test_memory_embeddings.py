from __future__ import annotations

import json

import httpx
import pytest

from book_os_core.memory_embeddings import (
    DeterministicFakeEmbeddingAdapter,
    EmbeddingGateway,
    EmbeddingOutputError,
    OpenAIEmbeddingAdapter,
    embedding_config_hash,
)
from book_os_core.secrets import DictSecretStore


def test_fake_embeddings_are_deterministic_and_mapping_can_prove_paraphrase() -> None:
    mapping = {
        "target text": [1.0, 0.0, 0.0],
        "semantic paraphrase": [0.99, 0.01, 0.0],
    }
    adapter = DeterministicFakeEmbeddingAdapter(mapping=mapping, dimension=3)
    gateway = EmbeddingGateway({"fake": adapter})

    first = gateway.embed(["target text", "other"], provider="fake", model="memory-test")
    second = gateway.embed(["target text", "other"], provider="fake", model="memory-test")

    assert first.vectors == second.vectors
    assert first.vectors[0] == [1.0, 0.0, 0.0]
    assert gateway.embed(["semantic paraphrase"], provider="fake", model="memory-test").vectors[
        0
    ] == [0.99, 0.01, 0.0]
    assert adapter.calls


def test_gateway_rejects_inconsistent_dimensions() -> None:
    adapter = DeterministicFakeEmbeddingAdapter(
        mapping={"a": [1.0, 0.0], "b": [1.0, 0.0, 0.0]}, dimension=2
    )
    gateway = EmbeddingGateway({"fake": adapter})
    with pytest.raises(EmbeddingOutputError, match="consistent dimension"):
        gateway.embed(["a", "b"], provider="fake", model="bad")


def test_embedding_config_hash_changes_with_model_or_dimension() -> None:
    base = embedding_config_hash("fake", "model-a", "v1", 8)
    assert base == embedding_config_hash("fake", "model-a", "v1", 8)
    assert base != embedding_config_hash("fake", "model-b", "v1", 8)
    assert base != embedding_config_hash("fake", "model-a", "v2", 8)
    assert base != embedding_config_hash("fake", "model-a", "v1", 16)


def test_openai_embedding_adapter_is_http_mocked_ordered_and_secret_safe() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("Authorization")
        body = json.loads(request.content)
        captured["body"] = body
        return httpx.Response(
            200,
            json={
                "object": "list",
                "model": "text-embedding-test-version",
                "data": [
                    {"object": "embedding", "index": 1, "embedding": [0.0, 1.0]},
                    {"object": "embedding", "index": 0, "embedding": [1.0, 0.0]},
                ],
                "usage": {"prompt_tokens": 7, "total_tokens": 7},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    secrets = DictSecretStore({"openai_api_key": "memory-super-secret"})
    adapter = OpenAIEmbeddingAdapter(
        secrets,
        client=client,
        endpoint="https://example.test/v1/embeddings",
    )
    gateway = EmbeddingGateway({"openai": adapter})
    result = gateway.embed(
        ["first text", "second text"], provider="openai", model="text-embedding-test"
    )

    assert result.vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert result.model_version == "text-embedding-test-version"
    assert result.usage["total_tokens"] == 7
    assert captured["authorization"] == "Bearer memory-super-secret"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body == {
        "model": "text-embedding-test",
        "input": ["first text", "second text"],
        "encoding_format": "float",
    }
    assert "memory-super-secret" not in json.dumps(body)
    assert "memory-super-secret" not in repr(result)
