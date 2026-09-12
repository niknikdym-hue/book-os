from __future__ import annotations

import json

import httpx

from book_os_core.model_gateway import AuthorityInputRef, ModelTaskRequest
from book_os_core.openai_production import OpenAIProductionResponsesAdapter
from book_os_core.prompts import SECTION_DRAFT_V1
from book_os_core.secrets import DictSecretStore


def _request(
    *, revision_hash: str = "a" * 64, objective: str = "Explain the mechanism"
) -> ModelTaskRequest:
    return ModelTaskRequest(
        task_id="01JTASK0000000000000000000",
        task_type="SECTION_DRAFT",
        role="WRITER",
        provider="openai",
        model="gpt-6-astra",
        prompt_id=SECTION_DRAFT_V1.prompt_id,
        prompt_version=SECTION_DRAFT_V1.version,
        prompt_hash=SECTION_DRAFT_V1.prompt_hash,
        section_objective=objective,
        authority_inputs=[
            AuthorityInputRef(
                revision_id="01JREV00000000000000000000",
                revision_hash=revision_hash,
                entity_type="chapter.contract",
            )
        ],
        authoritative_context={"chapter_contract": {"chapter_purpose": "Teach the mechanism"}},
        max_output_tokens=500,
        max_cost_usd=1.0,
    )


def test_prompt_cache_key_and_authority_prefix_are_stable_for_same_authority() -> None:
    adapter = OpenAIProductionResponsesAdapter(DictSecretStore({"openai_api_key": "test"}))

    first = adapter._body(_request(objective="First section"), SECTION_DRAFT_V1)
    second = adapter._body(_request(objective="Second section"), SECTION_DRAFT_V1)
    changed_authority = adapter._body(
        _request(revision_hash="b" * 64, objective="Second section"), SECTION_DRAFT_V1
    )

    assert first["prompt_cache_key"] == second["prompt_cache_key"]
    assert first["prompt_cache_key"] != changed_authority["prompt_cache_key"]
    assert str(first["prompt_cache_key"]).startswith("book-os:")
    assert len(str(first["prompt_cache_key"])) <= 64
    assert first["prompt_cache_options"] == {"mode": "explicit", "ttl": "30m"}

    first_input = first["input"]
    second_input = second["input"]
    assert isinstance(first_input, list)
    assert isinstance(second_input, list)
    assert first_input[0] == second_input[0]
    assert first_input[1] == second_input[1]
    assert first_input[2] != second_input[2]

    authority_message = first_input[1]
    assert isinstance(authority_message, dict)
    authority_content = authority_message["content"]
    assert isinstance(authority_content, list)
    authority_block = authority_content[0]
    assert isinstance(authority_block, dict)
    assert authority_block["prompt_cache_breakpoint"] == {"mode": "explicit"}
    authority_payload = json.loads(str(authority_block["text"]))
    assert authority_payload["authoritative_context"] == {
        "chapter_contract": {"chapter_purpose": "Teach the mechanism"}
    }

    dynamic_message = first_input[2]
    assert isinstance(dynamic_message, dict)
    dynamic_content = dynamic_message["content"]
    assert isinstance(dynamic_content, list)
    dynamic_block = dynamic_content[0]
    assert isinstance(dynamic_block, dict)
    dynamic_payload = json.loads(str(dynamic_block["text"]))
    assert dynamic_payload["section_objective"] == "First section"
    assert "authoritative_context" not in dynamic_payload


def test_cache_aware_cost_audit_uses_cached_and_cache_write_rates() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "resp_cache_fixture",
                "output_text": json.dumps({"text": "Cached draft", "notes": []}),
                "usage": {
                    "input_tokens": 1000,
                    "input_tokens_details": {
                        "cached_tokens": 600,
                        "cache_write_tokens": 200,
                    },
                    "output_tokens": 100,
                },
            },
        )

    adapter = OpenAIProductionResponsesAdapter(
        DictSecretStore({"openai_api_key": "cache-test-secret"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test/v1/responses",
    )
    result = adapter.generate(_request(), SECTION_DRAFT_V1)

    body = captured["body"]
    assert isinstance(body, dict)
    assert body["prompt_cache_options"] == {"mode": "explicit", "ttl": "30m"}
    assert body["prompt_cache_key"].startswith("book-os:")
    assert "cache-test-secret" not in json.dumps(body)

    guard = result.usage["cost_guard"]
    assert guard["input_usd_per_million"] == 10.0
    assert guard["cached_input_usd_per_million"] == 1.0
    assert guard["cache_write_usd_per_million"] == 12.5
    assert guard["output_usd_per_million"] == 50.0
    assert guard["uncached_input_tokens"] == 200
    assert guard["cached_input_tokens"] == 600
    assert guard["cache_write_tokens"] == 200
    assert guard["estimated_actual_cost_usd"] == 0.0101
    assert guard["pricing_source_date"] == "2026-09-09"
