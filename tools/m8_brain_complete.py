from pathlib import Path

p = Path('services/local-core/src/book_os_core/provider_lane.py')
s = p.read_text()
if '    ModelGateway,\n' not in s:
    s = s.replace('    ModelAdapterResult,\n', '    ModelAdapterResult,\n    ModelGateway,\n')

start = s.index('@dataclass(frozen=True)\nclass RouteDecision:')
end = s.index('\n\nclass ProviderLaneService:')
policy = '''@dataclass(frozen=True)
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
'''
s = s[:start] + policy + s[end:]

start = s.index('    def capabilities(')
end = s.index('\n\ndef _validated_output', start)
methods = '''    def capabilities(self, *, role: str | None = None) -> tuple[ProviderCapability, ...]:
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
'''
s = s[:start] + methods + s[end:]
p.write_text(s)

p = Path('services/local-core/src/book_os_core/model_gateway.py')
s = p.read_text().replace(
    'role: Literal["WRITER", "EVALUATOR"]',
    'role: Literal["WRITER", "EDITOR", "EVALUATOR"]',
)
p.write_text(s)

p = Path('services/local-core/src/book_os_core/app.py')
s = p.read_text()
s = s.replace(
    'from .provider_lane import RussiaPolicy, seed_capabilities\nfrom .provider_lane import ProviderLaneService\n',
    'from .provider_lane import (\n    GigaChatAdapter,\n    GigaChatEmbeddingAdapter,\n    ProviderLaneService,\n    RussiaPolicy,\n    YandexAdapter,\n    YandexEmbeddingAdapter,\n    seed_capabilities,\n)\n',
)
old = '''    projects = ProjectService(configured_data_dir) if configured_data_dir is not None else None
    configured_gateway = gateway or ModelGateway(
        {"openai": OpenAIResponsesAdapter(MacOSKeychainSecretStore())}
    )
'''
new = '''    projects = ProjectService(configured_data_dir) if configured_data_dir is not None else None
    provider_secrets = MacOSKeychainSecretStore()
    gigachat_generation = GigaChatAdapter(provider_secrets)
    configured_gateway = gateway or ModelGateway(
        {
            "openai": OpenAIResponsesAdapter(provider_secrets),
            "yandex": YandexAdapter(provider_secrets),
            "gigachat": gigachat_generation,
        }
    )
'''
if old not in s:
    raise SystemExit('gateway bootstrap snippet not found')
s = s.replace(old, new)
old = '''    configured_embedding_gateway = embedding_gateway or EmbeddingGateway(
        {"openai": OpenAIEmbeddingAdapter(MacOSKeychainSecretStore())}
    )
'''
new = '''    configured_embedding_gateway = embedding_gateway or EmbeddingGateway(
        {
            "openai": OpenAIEmbeddingAdapter(provider_secrets),
            "yandex": YandexEmbeddingAdapter(provider_secrets),
            "gigachat": GigaChatEmbeddingAdapter(gigachat_generation),
        }
    )
'''
if old not in s:
    raise SystemExit('embedding bootstrap snippet not found')
s = s.replace(old, new)
old = '''        return {
            "available": decision.available,
            "reason": decision.reason,
            "provider": decision.capability.provider if decision.capability else None,
            "model": decision.capability.model if decision.capability else None,
        }

    @app.get("/api/projects")
'''
new = '''        return {
            "available": decision.available,
            "reason": decision.reason,
            "provider": decision.capability.provider if decision.capability else None,
            "model": decision.capability.model if decision.capability else None,
            "config_id": decision.capability.config_id if decision.capability else None,
            "promotion": decision.capability.promotion if decision.capability else None,
            "attempts": [attempt.__dict__.copy() for attempt in decision.attempts],
        }

    @app.get("/api/provider-lane/promotions")
    def provider_promotions(_: None = Depends(require_token)) -> list[dict[str, str]]:
        return provider_lane.promotion_evidence() if provider_lane else []

    @app.get("/api/provider-lane/probes")
    def provider_probes(_: None = Depends(require_token)) -> list[dict[str, str]]:
        return provider_lane.probe_evidence() if provider_lane else []

    @app.get("/api/provider-lane/readiness")
    def provider_readiness(_: None = Depends(require_token)) -> dict[str, object]:
        roles: dict[str, dict[str, object]] = {}
        for role in ("WRITER", "EDITOR", "EVALUATOR"):
            decision = (
                provider_lane.route(role)
                if provider_lane
                else RussiaPolicy().route(seed_capabilities(), role=role)
            )
            roles[role] = {
                "available": decision.available,
                "reason": decision.reason,
                "provider": decision.capability.provider if decision.capability else None,
                "model": decision.capability.model if decision.capability else None,
            }
        return {
            "region": "RU",
            "ready": all(bool(value["available"]) for value in roles.values()),
            "roles": roles,
        }

    @app.get("/api/projects")
'''
if old not in s:
    raise SystemExit('provider API snippet not found')
s = s.replace(old, new)
p.write_text(s)

p = Path('docs/tasks/CODEX_TASK_009_RUSSIA_PROVIDER_LANE.md')
s = p.read_text().replace(
    '### A. Migration `0010` / regional provider evidence persistence',
    '### A. Migration `0009` / regional provider evidence persistence',
)
p.write_text(s)

Path('services/local-core/tests/test_provider_lane.py').write_text(r'''from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
import pytest

from book_os_core.app import create_app
from book_os_core.db import create_database
from book_os_core.memory_embeddings import EmbeddingGateway, EmbeddingOutputError
from book_os_core.model_gateway import (
    AuthorityInputRef,
    DeterministicFakeAdapter,
    ModelGateway,
    ModelOutputError,
    ModelProviderError,
    ModelTaskRequest,
)
from book_os_core.prompts import SECTION_DRAFT_V1
from book_os_core.provider_lane import (
    GigaChatAdapter,
    GigaChatEmbeddingAdapter,
    ProviderLaneService,
    RussiaPolicy,
    YandexAdapter,
    YandexEmbeddingAdapter,
    run_live_probe,
    seed_capabilities,
)
from book_os_core.secrets import DictSecretStore


def request(provider: str, model: str, *, role: str = "WRITER") -> ModelTaskRequest:
    return ModelTaskRequest(
        task_id="m8-test",
        task_type="SECTION_DRAFT",
        role=role,
        provider=provider,
        model=model,
        prompt_id=SECTION_DRAFT_V1.prompt_id,
        prompt_version=SECTION_DRAFT_V1.version,
        prompt_hash=SECTION_DRAFT_V1.prompt_hash,
        section_objective="Synthetic M8 test",
        authority_inputs=[
            AuthorityInputRef(
                revision_id="r", revision_hash="a" * 64, entity_type="chapter.contract"
            )
        ],
        authoritative_context={},
    )


def test_ru_policy_rejects_unpromoted_and_openai_without_vpn_fallback() -> None:
    decision = RussiaPolicy().route(seed_capabilities(), role="WRITER")
    assert not decision.available
    assert decision.reason == "QUALITY_NOT_PROMOTED"
    openai = next(item for item in seed_capabilities() if item.provider == "openai")
    blocked = RussiaPolicy().route((openai,), role="WRITER")
    assert not blocked.available
    assert blocked.reason == "REGION_NOT_SUPPORTED"
    assert all("VPN" not in attempt.reason for attempt in blocked.attempts)


def test_deterministic_fallback_uses_only_eligible_promoted_healthy_route() -> None:
    yandex = next(item for item in seed_capabilities() if item.provider == "yandex")
    giga = next(
        item for item in seed_capabilities() if item.provider == "gigachat" and item.commercial
    )
    candidates = (
        replace(yandex, promotion="PROMOTED", health="UNAVAILABLE"),
        replace(giga, promotion="PROMOTED", health="HEALTHY"),
    )
    decision = RussiaPolicy().route(candidates, role="WRITER")
    assert decision.available
    assert decision.capability is not None
    assert decision.capability.provider == "gigachat"
    assert any(attempt.reason == "PROVIDER_UNAVAILABLE" for attempt in decision.attempts)
    assert decision.attempts[-1].reason == "SELECTED"


def test_yandex_mocked_response_errors_and_secret_safety() -> None:
    def success(http_request: httpx.Request) -> httpx.Response:
        assert http_request.headers["Authorization"] == "Api-Key test-key"
        return httpx.Response(
            200,
            json={
                "id": "yc-1",
                "result": {"text": "Synthetic", "notes": []},
                "usage": {"tokens": 2},
            },
        )

    adapter = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "test-key"}),
        client=httpx.Client(transport=httpx.MockTransport(success)),
    )
    result = adapter.generate(request("yandex", "gpt://folder/yandexgpt/latest"), SECTION_DRAFT_V1)
    assert result.output["text"] == "Synthetic"
    assert "test-key" not in repr(result)

    missing = YandexAdapter(
        DictSecretStore({}), client=httpx.Client(transport=httpx.MockTransport(success))
    )
    with pytest.raises(ModelProviderError, match="credential"):
        missing.generate(request("yandex", "m"), SECTION_DRAFT_V1)

    malformed = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "key"}),
        client=httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"result": {"notes": []}}))
        ),
    )
    with pytest.raises(ModelOutputError, match="schema"):
        malformed.generate(request("yandex", "m"), SECTION_DRAFT_V1)


def test_gigachat_mocked_oauth_cache_rate_limit_and_secret_safety() -> None:
    calls: list[str] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(str(http_request.url))
        if http_request.url.path.endswith("oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        return httpx.Response(
            200,
            json={
                "id": "gc-1",
                "choices": [
                    {"message": {"content": json.dumps({"text": "Synthetic", "notes": []})}}
                ],
            },
        )

    adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "test-auth"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test",
    )
    assert adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1).output[
        "text"
    ] == "Synthetic"
    assert adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1).output[
        "text"
    ] == "Synthetic"
    assert sum(url.endswith("oauth") for url in calls) == 1
    assert "test-auth" not in repr(adapter)

    def limited(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("oauth"):
            return httpx.Response(200, json={"access_token": "access"})
        return httpx.Response(429, json={"error": "rate limited"})

    limited_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(limited)),
        endpoint="https://example.test",
    )
    with pytest.raises(ModelProviderError, match="429"):
        limited_adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)


def test_live_runner_is_never_implicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)
    with pytest.raises(RuntimeError, match="BOOK_OS_ALLOW_LIVE_PROVIDER"):
        run_live_probe()


def test_mocked_embedding_adapters_return_exact_model_identity_and_validate_output() -> None:
    def yandex(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"model": "yandex-v1", "embeddings": [{"embedding": [0.1, 0.2]}]}
        )

    yandex_gateway = EmbeddingGateway(
        {
            "yandex": YandexEmbeddingAdapter(
                DictSecretStore({"yandex_ai_studio_api_key": "key"}),
                client=httpx.Client(transport=httpx.MockTransport(yandex)),
            )
        }
    )
    assert yandex_gateway.embed(["synthetic"], provider="yandex", model="m").model_version == "yandex-v1"

    malformed_gateway = EmbeddingGateway(
        {
            "yandex": YandexEmbeddingAdapter(
                DictSecretStore({"yandex_ai_studio_api_key": "key"}),
                client=httpx.Client(
                    transport=httpx.MockTransport(
                        lambda _: httpx.Response(200, json={"embeddings": [{}]})
                    )
                ),
            )
        }
    )
    with pytest.raises(EmbeddingOutputError):
        malformed_gateway.embed(["synthetic"], provider="yandex", model="m")

    def giga(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("oauth"):
            return httpx.Response(200, json={"access_token": "access"})
        return httpx.Response(
            200, json={"model": "giga-v1", "data": [{"embedding": [0.1, 0.2]}]}
        )

    giga_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(giga)),
        endpoint="https://example.test",
    )
    giga_gateway = EmbeddingGateway({"gigachat": GigaChatEmbeddingAdapter(giga_adapter)})
    assert giga_gateway.embed(["synthetic"], provider="gigachat", model="m").model_version == "giga-v1"


def test_persisted_role_promotion_probe_overlay_and_gateway_execution(tmp_path: Path) -> None:
    service = ProviderLaneService(create_database(tmp_path / "provider.sqlite"))
    dataset = "d" * 64
    service.record_promotion(
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        role="WRITER",
        decision="PROMOTED",
        dataset_hash=dataset,
        scorecard_ref="scorecard:writer",
        quality_floor_passed=True,
        reason="synthetic Stage A evidence",
        actor="CENTRAL_BRAIN_TEST",
    )
    service.record_probe(
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        capability="generation",
        outcome="SUCCESS",
    )
    writer = service.route("WRITER")
    assert writer.available
    assert writer.capability is not None and writer.capability.provider == "yandex"
    editor = service.route("EDITOR")
    assert not editor.available
    assert editor.reason == "QUALITY_NOT_PROMOTED"

    gateway = ModelGateway({"yandex": DeterministicFakeAdapter()})
    result = service.generate_ru(gateway, request("ignored", "ignored"), SECTION_DRAFT_V1)
    assert result.output["text"].startswith("Draft for:")

    with pytest.raises(ValueError, match="quality floor"):
        service.record_promotion(
            provider="gigachat",
            model="GigaChat-2-Pro",
            config_id="b2b",
            region="RU",
            role="WRITER",
            decision="PROMOTED",
            dataset_hash=dataset,
            scorecard_ref="scorecard:giga",
            quality_floor_passed=False,
            reason="blocked",
            actor="CENTRAL_BRAIN_TEST",
        )
    with pytest.raises(ValueError, match="region/legal/commercial"):
        service.record_promotion(
            provider="openai",
            model="gpt-4.1",
            config_id="development",
            region="RU",
            role="WRITER",
            decision="PROMOTED",
            dataset_hash=dataset,
            scorecard_ref="scorecard:openai",
            quality_floor_passed=True,
            reason="not permitted",
            actor="CENTRAL_BRAIN_TEST",
        )


def test_provider_lane_api_is_authenticated_secret_safe_and_structured(tmp_path: Path) -> None:
    client = TestClient(create_app("test-token", tmp_path))
    assert client.get("/api/provider-lane/capabilities").status_code == 401
    headers = {"Authorization": "Bearer test-token"}
    capabilities = client.get("/api/provider-lane/capabilities", headers=headers)
    assert capabilities.status_code == 200
    body = capabilities.json()
    assert any(item["provider"] == "yandex" for item in body)
    route = client.post(
        "/api/provider-lane/route", headers=headers, json={"role": "WRITER", "embeddings": False}
    )
    assert route.status_code == 200
    assert route.json()["available"] is False
    assert isinstance(route.json()["attempts"], list)
    readiness = client.get("/api/provider-lane/readiness", headers=headers)
    assert readiness.status_code == 200
    assert readiness.json()["region"] == "RU"
    assert readiness.json()["ready"] is False
    assert client.get("/api/provider-lane/promotions", headers=headers).status_code == 200
    assert client.get("/api/provider-lane/probes", headers=headers).status_code == 200
    serialized = json.dumps(
        {
            "capabilities": body,
            "route": route.json(),
            "readiness": readiness.json(),
        }
    )
    assert "test-token" not in serialized
    assert "use vpn" not in serialized.lower()
''')
