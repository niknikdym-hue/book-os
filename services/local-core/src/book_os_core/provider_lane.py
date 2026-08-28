"""M8 policy, capability, and mocked-provider boundary. No live calls occur implicitly."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Literal, cast

import httpx
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .model_gateway import (
    ModelAdapterResult,
    ModelOutputError,
    ModelProviderError,
    ModelTaskRequest,
    OpenAIResponsesAdapter,
)
from .memory_embeddings import EmbeddingBatchResult, EmbeddingOutputError, EmbeddingProviderError
from .prompts import PromptTemplate
from .secrets import SecretStore

PROMOTION = Literal["CANDIDATE", "EVALUATED", "PROMOTED", "REJECTED", "EXPIRED"]


@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    model: str
    config_id: str
    region: str
    roles: tuple[str, ...]
    generation: bool
    embeddings: bool
    structured_output: bool
    tools: bool
    legal: bool
    commercial: bool
    privacy_ok: bool
    health: str
    promotion: PROMOTION
    matrix_version: str = "m8-2026-08-27"
    verified_at: str = "2026-08-27"
    sources: tuple[str, ...] = ()


def seed_capabilities() -> tuple[ProviderCapability, ...]:
    return (
        ProviderCapability(
            "yandex",
            "yandexgpt",
            "latest-discovery",
            "RU",
            ("WRITER", "EDITOR", "EVALUATOR"),
            True,
            True,
            True,
            False,
            True,
            True,
            True,
            "UNKNOWN",
            "CANDIDATE",
            sources=("https://yandex.cloud/en/docs/overview/api",),
        ),
        ProviderCapability(
            "gigachat",
            "GigaChat-2-Pro",
            "b2b",
            "RU",
            ("WRITER", "EDITOR", "EVALUATOR"),
            True,
            True,
            True,
            False,
            True,
            True,
            True,
            "UNKNOWN",
            "CANDIDATE",
            sources=(
                "https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api",
            ),
        ),
        ProviderCapability(
            "gigachat",
            "GigaChat-3-Ultra",
            "freemium",
            "RU",
            ("WRITER",),
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            "UNKNOWN",
            "REJECTED",
        ),
        ProviderCapability(
            "openai",
            "gpt-4.1",
            "development",
            "RU",
            ("WRITER", "EVALUATOR"),
            True,
            True,
            True,
            True,
            False,
            False,
            True,
            "UNKNOWN",
            "CANDIDATE",
        ),
    )


@dataclass(frozen=True)
class RouteDecision:
    available: bool
    reason: str | None
    capability: ProviderCapability | None


class RussiaPolicy:
    def route(
        self,
        capabilities: tuple[ProviderCapability, ...],
        *,
        role: str,
        require_embeddings: bool = False,
    ) -> RouteDecision:
        reasons: list[str] = []
        for item in capabilities:
            if item.region != "RU" or not item.legal:
                reasons.append("REGION_NOT_SUPPORTED")
                continue
            if not item.commercial:
                reasons.append("COMMERCIAL_PATH_NOT_VERIFIED")
                continue
            if not item.privacy_ok:
                reasons.append("PRIVACY_POLICY_NOT_VERIFIED")
                continue
            if role not in item.roles or (require_embeddings and not item.embeddings):
                reasons.append("CAPABILITY_MISSING")
                continue
            if item.promotion != "PROMOTED":
                reasons.append("QUALITY_NOT_PROMOTED")
                continue
            if item.health != "HEALTHY":
                reasons.append("PROVIDER_UNAVAILABLE")
                continue
            return RouteDecision(True, None, item)
        return RouteDecision(
            False,
            next(
                (
                    value
                    for value in (
                        "QUALITY_NOT_PROMOTED",
                        "COMMERCIAL_PATH_NOT_VERIFIED",
                        "REGION_NOT_SUPPORTED",
                    )
                    if value in reasons
                ),
                "PROVIDER_UNAVAILABLE",
            ),
            None,
        )


class ProviderLaneService:
    """Persistent M8 read model; bootstrap facts are versioned records, not routing truth."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._seed_if_empty()

    @staticmethod
    def _identity(item: ProviderCapability) -> str:
        return hashlib.sha256(
            f"{item.provider}|{item.model}|{item.config_id}|{item.region}".encode()
        ).hexdigest()[:26]

    def _seed_if_empty(self) -> None:
        with self.engine.begin() as connection:
            for item in seed_capabilities():
                payload = {
                    "roles": item.roles,
                    "generation": item.generation,
                    "embeddings": item.embeddings,
                    "structured_output": item.structured_output,
                    "tools": item.tools,
                    "legal": item.legal,
                    "commercial": item.commercial,
                    "privacy_ok": item.privacy_ok,
                    "promotion": item.promotion,
                }
                connection.execute(
                    text(
                        "INSERT OR IGNORE INTO provider_capabilities (capability_id, provider, model, config_id, matrix_version, matrix_hash, region, policy_json, capabilities_json, privacy_json, sources_json, verified_at, health_state, cost_json, current_state) VALUES (:id,:provider,:model,:config,:version,:hash,:region,:policy,:caps,:privacy,:sources,:verified,:health,:cost,'CURRENT')"
                    ),
                    {
                        "id": self._identity(item),
                        "provider": item.provider,
                        "model": item.model,
                        "config": item.config_id,
                        "version": item.matrix_version,
                        "hash": hashlib.sha256(repr(payload).encode()).hexdigest(),
                        "region": item.region,
                        "policy": json.dumps(
                            {
                                "legal": item.legal,
                                "commercial": item.commercial,
                                "promotion": item.promotion,
                            }
                        ),
                        "caps": json.dumps(payload),
                        "privacy": json.dumps({"privacy_ok": item.privacy_ok}),
                        "sources": json.dumps(item.sources),
                        "verified": item.verified_at,
                        "health": item.health,
                        "cost": "{}",
                    },
                )

    def capabilities(self) -> tuple[ProviderCapability, ...]:
        with self.engine.connect() as connection:
            promotion_rows = (
                connection.execute(
                    text(
                        "SELECT provider, model, config_id, region, decision FROM provider_role_promotions WHERE superseded_at IS NULL"
                    )
                )
                .mappings()
                .all()
            )
            promoted = {
                (str(row["provider"]), str(row["model"]), str(row["config_id"]), str(row["region"]))
                for row in promotion_rows
                if row["decision"] == "PROMOTED"
            }
            rows = connection.execute(
                text(
                    "SELECT provider, model, config_id, region, matrix_version, verified_at, health_state, policy_json, capabilities_json, privacy_json, sources_json FROM provider_capabilities WHERE current_state='CURRENT' AND superseded_at IS NULL"
                )
            ).mappings()
            result = []
            for row in rows:
                policy, caps, privacy = (
                    json.loads(row["policy_json"]),
                    json.loads(row["capabilities_json"]),
                    json.loads(row["privacy_json"]),
                )
                identity = (
                    str(row["provider"]),
                    str(row["model"]),
                    str(row["config_id"]),
                    str(row["region"]),
                )
                raw_promotion = str(policy["promotion"])
                if raw_promotion not in (
                    "CANDIDATE", "EVALUATED", "PROMOTED", "REJECTED", "EXPIRED"
                ):
                    raise ValueError(f"invalid persisted promotion state: {raw_promotion}")
                promotion: PROMOTION = (
                    "PROMOTED" if identity in promoted else cast(PROMOTION, raw_promotion)
                )
                result.append(
                    ProviderCapability(
                        str(row["provider"]),
                        str(row["model"]),
                        str(row["config_id"]),
                        str(row["region"]),
                        tuple(caps["roles"]),
                        bool(caps["generation"]),
                        bool(caps["embeddings"]),
                        bool(caps["structured_output"]),
                        bool(caps["tools"]),
                        bool(policy["legal"]),
                        bool(policy["commercial"]),
                        bool(privacy["privacy_ok"]),
                        str(row["health_state"]),
                        promotion,
                        str(row["matrix_version"]),
                        str(row["verified_at"]),
                        tuple(json.loads(row["sources_json"])),
                    )
                )
        return tuple(result)

    def route(self, role: str, *, embeddings: bool = False) -> RouteDecision:
        return RussiaPolicy().route(self.capabilities(), role=role, require_embeddings=embeddings)

    def promotion_evidence(self) -> list[dict[str, str]]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT provider, model, config_id, region, role, dataset_hash, scorecard_ref, decision, reason, independence_state, matrix_hash, actor, created_at FROM provider_role_promotions ORDER BY created_at DESC"
                )
            ).mappings()
            return [{key: str(value) for key, value in row.items()} for row in rows]

    def record_promotion(
        self,
        *,
        provider: str,
        model: str,
        config_id: str,
        region: str,
        role: str,
        decision: Literal["CANDIDATE", "EVALUATED", "PROMOTED", "REJECTED"],
        dataset_hash: str,
        scorecard_ref: str,
        quality_floor_passed: bool,
        reason: str,
        actor: str,
    ) -> None:
        if decision == "PROMOTED" and not quality_floor_passed:
            raise ValueError("quality floor failure cannot be promoted")
        now = datetime.now(timezone.utc).isoformat()
        promotion_id = hashlib.sha256(
            f"{provider}|{model}|{config_id}|{role}|{now}".encode()
        ).hexdigest()[:26]
        persisted = decision if decision in ("PROMOTED", "REJECTED") else "REJECTED"
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO provider_role_promotions (promotion_id, provider, model, config_id, region, role, dataset_hash, scorecard_ref, decision, reason, independence_state, matrix_hash, actor, created_at) VALUES (:id,:provider,:model,:config,:region,:role,:dataset,:scorecard,:decision,:reason,'UNKNOWN','m8-stage-a',:actor,:created)"
                ),
                {
                    "id": promotion_id,
                    "provider": provider,
                    "model": model,
                    "config": config_id,
                    "region": region,
                    "role": role,
                    "dataset": dataset_hash,
                    "scorecard": scorecard_ref,
                    "decision": persisted,
                    "reason": reason,
                    "actor": actor,
                    "created": now,
                },
            )


def _validated_output(request: ModelTaskRequest, payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("result") or payload.get("output") or payload.get("text")
    if isinstance(raw, dict):
        value = raw
    elif isinstance(raw, str):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ModelOutputError("provider structured output is not JSON") from exc
    else:
        raise ModelOutputError("provider response has no structured output")
    # The existing gateway uses strict JSON schemas; malformed M8 structured output is rejected.
    if request.task_type == "SECTION_DRAFT" and (
        not isinstance(value.get("text"), str) or not value["text"]
    ):
        raise ModelOutputError("provider output failed schema validation")
    return value


class YandexAdapter:
    provider_name = "yandex"

    def __init__(
        self,
        secrets: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://ai.api.cloud.yandex.net/v1/foundationModels/v1/completion",
    ) -> None:
        self.secrets, self.client, self.endpoint = secrets, client or httpx.Client(), endpoint

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        try:
            key = self.secrets.get_secret("yandex_ai_studio_api_key")
        except Exception as exc:
            raise ModelProviderError("Yandex credential is unavailable") from exc
        response = self.client.post(
            self.endpoint,
            headers={"Authorization": f"Api-Key {key}"},
            json={
                "modelUri": request.model,
                "completionOptions": {"responseFormat": "JSON_OBJECT"},
                "messages": [
                    {"role": "system", "text": prompt.developer_text},
                    {"role": "user", "text": request.section_objective},
                ],
            },
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"Yandex HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("Yandex response must be an object")
        return ModelAdapterResult(
            str(payload.get("id")) if payload.get("id") else None,
            _validated_output(request, payload),
            payload.get("usage", {}) if isinstance(payload.get("usage"), dict) else {},
        )


class GigaChatAdapter:
    provider_name = "gigachat"

    def __init__(
        self,
        secrets: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://api.giga.chat",
        clock: Any = time.time,
    ) -> None:
        self.secrets = secrets
        self.client = client or httpx.Client()
        self.endpoint = endpoint.rstrip("/")
        self.clock = clock
        self._token: tuple[str, float] | None = None

    def _access_token(self) -> str:
        if self._token and self._token[1] > self.clock() + 5:
            return self._token[0]
        try:
            auth = self.secrets.get_secret("gigachat_authorization_key")
        except Exception as exc:
            raise ModelProviderError("GigaChat credential is unavailable") from exc
        response = self.client.post(
            f"{self.endpoint}/api/v2/oauth",
            headers={"Authorization": f"Basic {auth}", "RqUID": "book-os-m8"},
            data={"scope": "GIGACHAT_API_B2B"},
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"GigaChat token HTTP {response.status_code}")
        payload = response.json()
        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise ModelProviderError("GigaChat token response is malformed")
        self._token = (token, self.clock() + int(payload.get("expires_in", 1800)))
        return token

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        response = self.client.post(
            f"{self.endpoint}/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._access_token()}"},
            json={
                "model": request.model,
                "messages": [
                    {"role": "system", "content": prompt.developer_text},
                    {"role": "user", "content": request.section_objective},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "strict": True,
                        "schema": OpenAIResponsesAdapter.output_schema(request.task_type),
                    },
                },
            },
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"GigaChat HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("GigaChat response must be an object")
        choice = payload.get("choices", [{}])
        content = (
            choice[0].get("message", {}).get("content")
            if isinstance(choice, list) and choice
            else None
        )
        return ModelAdapterResult(
            str(payload.get("id")) if payload.get("id") else None,
            _validated_output(request, {"output": content}),
            payload.get("usage", {}) if isinstance(payload.get("usage"), dict) else {},
        )


def _embedding_result(provider: str, model: str, payload: dict[str, Any]) -> EmbeddingBatchResult:
    data = payload.get("data") or payload.get("embeddings")
    if not isinstance(data, list):
        raise EmbeddingOutputError("provider embeddings response has no data array")
    vectors: list[list[float]] = []
    for item in data:
        raw = item.get("embedding") if isinstance(item, dict) else None
        if not isinstance(raw, list):
            raise EmbeddingOutputError("provider embedding item is malformed")
        try:
            vectors.append([float(value) for value in raw])
        except (TypeError, ValueError) as exc:
            raise EmbeddingOutputError("provider embedding is non-numeric") from exc
    return EmbeddingBatchResult(
        provider,
        model,
        str(payload.get("model") or model),
        vectors,
        payload.get("usage", {}) if isinstance(payload.get("usage"), dict) else {},
    )


class YandexEmbeddingAdapter:
    provider_name = "yandex"

    def __init__(
        self,
        secrets: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://ai.api.cloud.yandex.net/v1/foundationModels:embedText",
    ) -> None:
        self.secrets, self.client, self.endpoint = secrets, client or httpx.Client(), endpoint

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult:
        try:
            key = self.secrets.get_secret("yandex_ai_studio_api_key")
            response = self.client.post(
                self.endpoint,
                headers={"Authorization": f"Api-Key {key}"},
                json={"modelUri": model, "texts": texts},
            )
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError("Yandex embeddings request failed") from exc
        if response.status_code >= 400:
            raise EmbeddingProviderError(f"Yandex embeddings HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise EmbeddingOutputError("Yandex embeddings response must be an object")
        return _embedding_result(self.provider_name, model, payload)


class GigaChatEmbeddingAdapter:
    provider_name = "gigachat"

    def __init__(self, generation: GigaChatAdapter) -> None:
        self._generation = generation

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult:
        try:
            response = self._generation.client.post(
                f"{self._generation.endpoint}/api/v1/embeddings",
                headers={"Authorization": f"Bearer {self._generation._access_token()}"},
                json={"model": model, "input": texts},
            )
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError("GigaChat embeddings request failed") from exc
        if response.status_code >= 400:
            raise EmbeddingProviderError(f"GigaChat embeddings HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise EmbeddingOutputError("GigaChat embeddings response must be an object")
        return _embedding_result(self.provider_name, model, payload)


def run_live_probe() -> None:
    if os.environ.get("BOOK_OS_ALLOW_LIVE_PROVIDER") != "1":
        raise RuntimeError("live provider execution requires BOOK_OS_ALLOW_LIVE_PROVIDER=1")
    raise RuntimeError("live promotion requires explicit Central Brain execution context")
