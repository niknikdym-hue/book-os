"""M8 policy, capability, and mocked-provider boundary. No live calls occur implicitly."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, cast

import httpx
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .model_gateway import (
    ModelAdapterResult,
    ModelGateway,
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
class RouteAttempt:
    provider: str
    model: str
    config_id: str
    reason: str


@dataclass(frozen=True)
class RouteDecision:
    available: bool
    reason: str | None
    capability: ProviderCapability | None
    attempts: tuple[RouteAttempt, ...] = ()


class RussiaPolicy:
    def route(
        self,
        capabilities: tuple[ProviderCapability, ...],
        *,
        role: str,
        require_embeddings: bool = False,
    ) -> RouteDecision:
        attempts: list[RouteAttempt] = []
        reasons: list[str] = []
        ordered = sorted(
            capabilities,
            key=lambda item: (item.provider, item.model, item.config_id, item.region),
        )
        for item in ordered:
            reason: str | None = None
            if item.region != "RU" or not item.legal:
                reason = "REGION_NOT_SUPPORTED"
            elif not item.commercial:
                reason = "COMMERCIAL_PATH_NOT_VERIFIED"
            elif not item.privacy_ok:
                reason = "PRIVACY_POLICY_NOT_VERIFIED"
            elif role not in item.roles:
                reason = "CAPABILITY_MISSING"
            elif require_embeddings and not item.embeddings:
                reason = "CAPABILITY_MISSING"
            elif not require_embeddings and not item.generation:
                reason = "CAPABILITY_MISSING"
            elif item.promotion != "PROMOTED":
                reason = "QUALITY_NOT_PROMOTED"
            elif item.health != "HEALTHY":
                reason = "PROVIDER_UNAVAILABLE"

            if reason is not None:
                attempts.append(RouteAttempt(item.provider, item.model, item.config_id, reason))
                reasons.append(reason)
                continue
            attempts.append(RouteAttempt(item.provider, item.model, item.config_id, "SELECTED"))
            return RouteDecision(True, None, item, tuple(attempts))

        for priority in (
            "QUALITY_NOT_PROMOTED",
            "PROVIDER_UNAVAILABLE",
            "CAPABILITY_MISSING",
            "PRIVACY_POLICY_NOT_VERIFIED",
            "COMMERCIAL_PATH_NOT_VERIFIED",
            "REGION_NOT_SUPPORTED",
        ):
            if priority in reasons:
                return RouteDecision(False, priority, None, tuple(attempts))
        return RouteDecision(False, "PROVIDER_UNAVAILABLE", None, tuple(attempts))


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

    def capabilities(self, *, role: str | None = None) -> tuple[ProviderCapability, ...]:
        with self.engine.connect() as connection:
            promotion_by_identity: dict[tuple[str, str, str, str], PROMOTION] = {}
            if role is not None:
                promotion_rows = (
                    connection.execute(
                        text(
                            "SELECT provider, model, config_id, region, decision FROM provider_role_promotions WHERE role=:role AND superseded_at IS NULL ORDER BY created_at DESC"
                        ),
                        {"role": role},
                    )
                    .mappings()
                    .all()
                )
                for row in promotion_rows:
                    identity = (
                        str(row["provider"]),
                        str(row["model"]),
                        str(row["config_id"]),
                        str(row["region"]),
                    )
                    if identity in promotion_by_identity:
                        continue
                    raw_decision = str(row["decision"])
                    if raw_decision not in ("PROMOTED", "REJECTED", "EXPIRED"):
                        raise ValueError(f"invalid persisted promotion decision: {raw_decision}")
                    promotion_by_identity[identity] = cast(PROMOTION, raw_decision)

            health_by_identity: dict[tuple[str, str, str, str], str] = {}
            probe_rows = (
                connection.execute(
                    text(
                        "SELECT provider, model, config_id, region, outcome FROM provider_probe_runs ORDER BY created_at DESC"
                    )
                )
                .mappings()
                .all()
            )
            for row in probe_rows:
                identity = (
                    str(row["provider"]),
                    str(row["model"]),
                    str(row["config_id"]),
                    str(row["region"]),
                )
                if identity not in health_by_identity:
                    health_by_identity[identity] = (
                        "HEALTHY" if str(row["outcome"]) == "SUCCESS" else "UNAVAILABLE"
                    )

            rows = connection.execute(
                text(
                    "SELECT provider, model, config_id, region, matrix_version, verified_at, health_state, policy_json, capabilities_json, privacy_json, sources_json FROM provider_capabilities WHERE current_state='CURRENT' AND superseded_at IS NULL"
                )
            ).mappings()
            result: list[ProviderCapability] = []
            for row in rows:
                policy_data, caps, privacy = (
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
                raw_promotion = str(policy_data["promotion"])
                if raw_promotion not in (
                    "CANDIDATE",
                    "EVALUATED",
                    "PROMOTED",
                    "REJECTED",
                    "EXPIRED",
                ):
                    raise ValueError(f"invalid persisted promotion state: {raw_promotion}")
                promotion = promotion_by_identity.get(identity, cast(PROMOTION, raw_promotion))
                health = health_by_identity.get(identity, str(row["health_state"]))
                result.append(
                    ProviderCapability(
                        str(row["provider"]),
                        str(row["model"]),
                        str(row["config_id"]),
                        str(row["region"]),
                        tuple(str(value) for value in caps["roles"]),
                        bool(caps["generation"]),
                        bool(caps["embeddings"]),
                        bool(caps["structured_output"]),
                        bool(caps["tools"]),
                        bool(policy_data["legal"]),
                        bool(policy_data["commercial"]),
                        bool(privacy["privacy_ok"]),
                        health,
                        promotion,
                        str(row["matrix_version"]),
                        str(row["verified_at"]),
                        tuple(str(value) for value in json.loads(row["sources_json"])),
                    )
                )
        return tuple(result)

    def route(self, role: str, *, embeddings: bool = False) -> RouteDecision:
        return RussiaPolicy().route(
            self.capabilities(role=role), role=role, require_embeddings=embeddings
        )

    def promotion_evidence(self) -> list[dict[str, str]]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT promotion_id, provider, model, config_id, region, role, dataset_snapshot_id, dataset_hash, scorecard_ref, decision, reason, independence_state, matrix_hash, actor, created_at, superseded_at FROM provider_role_promotions ORDER BY created_at DESC"
                )
            ).mappings()
            return [
                {key: "" if value is None else str(value) for key, value in row.items()}
                for row in rows
            ]

    def probe_evidence(self) -> list[dict[str, str]]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT probe_id, provider, model, config_id, matrix_hash, probe_type, region, capability, latency_ms, usage_json, cost_json, outcome, external_request_id, created_at FROM provider_probe_runs ORDER BY created_at DESC"
                )
            ).mappings()
            return [
                {key: "" if value is None else str(value) for key, value in row.items()}
                for row in rows
            ]

    def _capability_row(
        self, *, provider: str, model: str, config_id: str, region: str
    ) -> dict[str, Any]:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT matrix_hash, policy_json, capabilities_json, privacy_json FROM provider_capabilities WHERE provider=:provider AND model=:model AND config_id=:config AND region=:region AND current_state='CURRENT' AND superseded_at IS NULL"
                    ),
                    {"provider": provider, "model": model, "config": config_id, "region": region},
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            raise ValueError("provider capability identity is not current")
        return dict(row)

    def record_promotion(
        self,
        *,
        provider: str,
        model: str,
        config_id: str,
        region: str,
        role: str,
        decision: Literal["PROMOTED", "REJECTED", "EXPIRED"],
        dataset_hash: str,
        scorecard_ref: str,
        quality_floor_passed: bool,
        reason: str,
        actor: str,
        dataset_snapshot_id: str | None = None,
        independence_state: str = "UNKNOWN",
    ) -> str:
        capability = self._capability_row(
            provider=provider, model=model, config_id=config_id, region=region
        )
        policy_data = json.loads(capability["policy_json"])
        caps = json.loads(capability["capabilities_json"])
        privacy = json.loads(capability["privacy_json"])
        if decision == "PROMOTED":
            if not quality_floor_passed:
                raise ValueError("quality floor failure cannot be promoted")
            if not bool(policy_data["legal"]) or not bool(policy_data["commercial"]):
                raise ValueError("region/legal/commercial gate blocks promotion")
            if not bool(privacy["privacy_ok"]):
                raise ValueError("privacy gate blocks promotion")
            if role not in tuple(str(value) for value in caps["roles"]):
                raise ValueError("role capability gate blocks promotion")
            if role == "EVALUATOR" and independence_state != "INDEPENDENT":
                raise ValueError("release-grade evaluator promotion requires independent evidence")
        if not dataset_hash or not scorecard_ref or not actor:
            raise ValueError("promotion evidence requires dataset, scorecard, and actor")

        now = datetime.now(timezone.utc).isoformat()
        promotion_id = hashlib.sha256(
            f"{provider}|{model}|{config_id}|{region}|{role}|{decision}|{now}".encode()
        ).hexdigest()[:26]
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE provider_role_promotions SET superseded_at=:now WHERE provider=:provider AND model=:model AND config_id=:config AND region=:region AND role=:role AND superseded_at IS NULL"
                ),
                {
                    "now": now,
                    "provider": provider,
                    "model": model,
                    "config": config_id,
                    "region": region,
                    "role": role,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO provider_role_promotions (promotion_id, provider, model, config_id, region, role, dataset_snapshot_id, dataset_hash, scorecard_ref, decision, reason, independence_state, matrix_hash, actor, created_at) VALUES (:id,:provider,:model,:config,:region,:role,:dataset_snapshot,:dataset,:scorecard,:decision,:reason,:independence,:matrix_hash,:actor,:created)"
                ),
                {
                    "id": promotion_id,
                    "provider": provider,
                    "model": model,
                    "config": config_id,
                    "region": region,
                    "role": role,
                    "dataset_snapshot": dataset_snapshot_id,
                    "dataset": dataset_hash,
                    "scorecard": scorecard_ref,
                    "decision": decision,
                    "reason": reason,
                    "independence": independence_state,
                    "matrix_hash": str(capability["matrix_hash"]),
                    "actor": actor,
                    "created": now,
                },
            )
        return promotion_id

    def record_probe(
        self,
        *,
        provider: str,
        model: str,
        config_id: str,
        region: str,
        capability: str,
        outcome: Literal["SUCCESS", "REFUSAL", "UNAVAILABLE", "ERROR"],
        probe_type: Literal["MOCK", "LIVE"] = "MOCK",
        latency_ms: int | None = None,
        usage: dict[str, Any] | None = None,
        cost: dict[str, Any] | None = None,
        external_request_id: str | None = None,
    ) -> str:
        if probe_type == "LIVE" and os.environ.get("BOOK_OS_ALLOW_LIVE_PROVIDER") != "1":
            raise RuntimeError("live provider execution requires BOOK_OS_ALLOW_LIVE_PROVIDER=1")
        current = self._capability_row(
            provider=provider, model=model, config_id=config_id, region=region
        )
        now = datetime.now(timezone.utc).isoformat()
        probe_id = hashlib.sha256(
            f"{provider}|{model}|{config_id}|{region}|{capability}|{probe_type}|{now}".encode()
        ).hexdigest()[:26]
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO provider_probe_runs (probe_id, provider, model, config_id, matrix_hash, probe_type, region, capability, latency_ms, usage_json, cost_json, outcome, external_request_id, created_at) VALUES (:id,:provider,:model,:config,:matrix_hash,:probe_type,:region,:capability,:latency,:usage,:cost,:outcome,:external,:created)"
                ),
                {
                    "id": probe_id,
                    "provider": provider,
                    "model": model,
                    "config": config_id,
                    "matrix_hash": str(current["matrix_hash"]),
                    "probe_type": probe_type,
                    "region": region,
                    "capability": capability,
                    "latency": latency_ms,
                    "usage": json.dumps(usage or {}),
                    "cost": json.dumps(cost or {}),
                    "outcome": outcome,
                    "external": external_request_id,
                    "created": now,
                },
            )
        return probe_id

    def generate_ru(
        self,
        gateway: ModelGateway,
        request: ModelTaskRequest,
        prompt: PromptTemplate,
    ) -> ModelAdapterResult:
        decision = self.route(request.role)
        return gateway.generate_ru(request, prompt, route=decision)


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
        endpoint: str = "https://ai.api.cloud.yandex.net/foundationModels/v1/completion",
    ) -> None:
        self.secrets = secrets
        self.client = client or httpx.Client()
        self.endpoint = endpoint

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        try:
            key = self.secrets.get_secret("yandex_ai_studio_api_key")
        except Exception as exc:
            raise ModelProviderError("Yandex credential is unavailable") from exc
        response = self.client.post(
            self.endpoint,
            headers={"Authorization": f"Api-Key {key}", "Content-Type": "application/json"},
            json={
                "modelUri": request.model,
                "completionOptions": {
                    "stream": False,
                    "maxTokens": str(request.max_output_tokens),
                },
                "messages": [
                    {"role": "system", "text": prompt.developer_text},
                    {"role": "user", "text": request.section_objective},
                ],
                "jsonSchema": {
                    "schema": OpenAIResponsesAdapter.output_schema(request.task_type),
                },
            },
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"Yandex HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("Yandex response must be an object")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ModelOutputError("Yandex response has no result object")
        alternatives = result.get("alternatives")
        if not isinstance(alternatives, list) or not alternatives:
            raise ModelOutputError("Yandex response has no alternatives")
        first = alternatives[0]
        message = first.get("message") if isinstance(first, dict) else None
        text_value = message.get("text") if isinstance(message, dict) else None
        if not isinstance(text_value, str) or not text_value:
            raise ModelOutputError("Yandex response has no generated text")
        usage_raw = result.get("usage")
        usage = dict(usage_raw) if isinstance(usage_raw, dict) else {}
        if result.get("modelVersion") is not None:
            usage["model_version"] = str(result["modelVersion"])
        return ModelAdapterResult(
            str(payload.get("id")) if payload.get("id") else None,
            _validated_output(request, {"output": text_value}),
            usage,
        )


class GigaChatAdapter:
    provider_name = "gigachat"
    _COMMERCIAL_SCOPES = {"GIGACHAT_API_B2B", "GIGACHAT_API_CORP"}

    def __init__(
        self,
        secrets: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://api.giga.chat",
        auth_endpoint: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        scope: str = "GIGACHAT_API_B2B",
        ca_bundle: str | None = None,
        clock: Any = time.time,
    ) -> None:
        if scope not in self._COMMERCIAL_SCOPES:
            raise ValueError("GigaChat product runtime requires a commercial B2B/CORP scope")
        self.secrets = secrets
        self.client = client or httpx.Client(verify=ca_bundle if ca_bundle is not None else True)
        self.endpoint = endpoint.rstrip("/")
        self.auth_endpoint = auth_endpoint
        self.scope = scope
        self.clock = clock
        self._token: tuple[str, float] | None = None

    def _token_expiry(self, payload: dict[str, Any]) -> float:
        expires_in = payload.get("expires_in")
        if isinstance(expires_in, (int, float)):
            return self.clock() + float(expires_in)
        expires_at = payload.get("expires_at")
        if isinstance(expires_at, (int, float)):
            value = float(expires_at)
            if value > 10_000_000_000:
                value /= 1000.0
            return value
        return self.clock() + 1800.0

    def _access_token(self) -> str:
        if self._token and self._token[1] > self.clock() + 5:
            return self._token[0]
        try:
            auth = self.secrets.get_secret("gigachat_authorization_key")
        except Exception as exc:
            raise ModelProviderError("GigaChat credential is unavailable") from exc
        response = self.client.post(
            self.auth_endpoint,
            headers={
                "Authorization": f"Basic {auth}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={"scope": self.scope},
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"GigaChat token HTTP {response.status_code}")
        payload = response.json()
        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise ModelProviderError("GigaChat token response is malformed")
        self._token = (token, self._token_expiry(payload))
        return token

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        response = self.client.post(
            f"{self.endpoint}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
            },
            json={
                "model": request.model,
                "messages": [
                    {"role": "system", "content": prompt.developer_text},
                    {"role": "user", "content": request.section_objective},
                ],
                "response_format": {
                    "type": "json_schema",
                    "schema": OpenAIResponsesAdapter.output_schema(request.task_type),
                    "strict": True,
                },
            },
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"GigaChat HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("GigaChat response must be an object")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ModelOutputError("GigaChat response has no choices")
        first = choices[0]
        finish_reason = str(first.get("finish_reason") or "")
        if finish_reason.casefold() in {"blacklist", "content_filter", "refusal"}:
            raise ModelProviderError(f"GigaChat refusal: {finish_reason}")
        message = first.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        usage_raw = payload.get("usage")
        usage = dict(usage_raw) if isinstance(usage_raw, dict) else {}
        if payload.get("model") is not None:
            usage["model_version"] = str(payload["model"])
        return ModelAdapterResult(
            str(payload.get("id")) if payload.get("id") else None,
            _validated_output(request, {"output": content}),
            usage,
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
        endpoint: str = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding",
    ) -> None:
        self.secrets = secrets
        self.client = client or httpx.Client()
        self.endpoint = endpoint

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult:
        try:
            key = self.secrets.get_secret("yandex_ai_studio_api_key")
        except Exception as exc:
            raise EmbeddingProviderError("Yandex embedding credential is unavailable") from exc
        vectors: list[list[float]] = []
        model_version: str | None = None
        total_tokens = 0
        for text_value in texts:
            try:
                response = self.client.post(
                    self.endpoint,
                    headers={"Authorization": f"Api-Key {key}", "Content-Type": "application/json"},
                    json={"modelUri": model, "text": text_value},
                )
            except httpx.HTTPError as exc:
                raise EmbeddingProviderError("Yandex embeddings request failed") from exc
            if response.status_code >= 400:
                raise EmbeddingProviderError(f"Yandex embeddings HTTP {response.status_code}")
            payload = response.json()
            if not isinstance(payload, dict):
                raise EmbeddingOutputError("Yandex embeddings response must be an object")
            raw_vector = payload.get("embedding")
            if not isinstance(raw_vector, list):
                raise EmbeddingOutputError("Yandex embedding item is malformed")
            try:
                vectors.append([float(value) for value in raw_vector])
            except (TypeError, ValueError) as exc:
                raise EmbeddingOutputError("Yandex embedding is non-numeric") from exc
            returned_version = str(payload.get("modelVersion") or model)
            if model_version is None:
                model_version = returned_version
            elif returned_version != model_version:
                raise EmbeddingOutputError("Yandex embeddings returned inconsistent model versions")
            try:
                total_tokens += int(payload.get("numTokens") or 0)
            except (TypeError, ValueError):
                pass
        return EmbeddingBatchResult(
            self.provider_name,
            model,
            model_version or model,
            vectors,
            {"input_count": len(texts), "input_tokens": total_tokens},
        )


class GigaChatEmbeddingAdapter:
    provider_name = "gigachat"

    def __init__(self, generation: GigaChatAdapter) -> None:
        self._generation = generation

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult:
        try:
            response = self._generation.client.post(
                f"{self._generation.endpoint}/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._generation._access_token()}",
                    "Content-Type": "application/json",
                },
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
