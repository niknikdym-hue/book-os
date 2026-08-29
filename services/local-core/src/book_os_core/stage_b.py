"""M8 Stage B pre-live orchestration.

This module is intentionally fail-closed: ordinary startup/tests never enable real
provider execution.  It builds an exact, secret-safe plan, enforces every
provider HTTP call through a budgeted transport, separates LIVE health evidence
from MOCK evidence, and produces role-gate evidence without self-promotion.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Literal, Sequence

import httpx
from sqlalchemy import text

from .bookbench import BookBenchReport
from .memory_embeddings import EmbeddingAdapter
from .model_gateway import ModelAdapter
from .provider_lane import (
    GigaChatAdapter,
    GigaChatEmbeddingAdapter,
    ProviderCapability,
    ProviderLaneService,
    RussiaPolicy,
    YandexAdapter,
    YandexEmbeddingAdapter,
)
from .secrets import SecretStore

CallKind = Literal["AUTH", "DISCOVERY", "GENERATION", "EMBEDDING"]
CredentialState = Literal["AVAILABLE", "NOT AVAILABLE"]
HealthState = Literal["HEALTHY", "UNAVAILABLE", "UNKNOWN"]


class StageBError(RuntimeError):
    pass


class StageBGateError(StageBError):
    pass


class StageBBudgetExceeded(StageBGateError):
    pass


class StageBPlanMismatch(StageBGateError):
    pass


@dataclass(frozen=True)
class StageBCandidate:
    provider: str
    model: str
    config_id: str
    region: str
    roles: tuple[str, ...]
    require_embeddings: bool = False


@dataclass(frozen=True)
class StageBBudget:
    max_generation_requests: int
    max_embedding_requests: int
    max_total_requests: int
    max_auth_requests: int = 0
    max_discovery_requests: int = 0
    max_estimated_cost: float | None = None
    max_actual_cost: float | None = None

    def validate(self) -> None:
        values = (
            self.max_generation_requests,
            self.max_embedding_requests,
            self.max_total_requests,
            self.max_auth_requests,
            self.max_discovery_requests,
        )
        if min(values) < 0:
            raise ValueError("request budget cannot be negative")
        bounded_sum = (
            self.max_generation_requests
            + self.max_embedding_requests
            + self.max_auth_requests
            + self.max_discovery_requests
        )
        if self.max_total_requests <= 0 or self.max_total_requests < bounded_sum:
            raise ValueError("total request budget must cover every bounded provider call")
        if self.max_estimated_cost is not None and self.max_estimated_cost < 0:
            raise ValueError("estimated cost budget cannot be negative")
        if self.max_actual_cost is not None and self.max_actual_cost < 0:
            raise ValueError("actual cost budget cannot be negative")

    def public_dict(self) -> dict[str, object]:
        return {
            "generation_requests_max": self.max_generation_requests,
            "embedding_requests_max": self.max_embedding_requests,
            "auth_requests_max": self.max_auth_requests,
            "discovery_requests_max": self.max_discovery_requests,
            "total_requests_max": self.max_total_requests,
            "estimated_cost_max": self.max_estimated_cost,
            "actual_cost_max": self.max_actual_cost,
        }


@dataclass
class StageBBudgetLedger:
    limits: StageBBudget
    generation_requests: int = 0
    embedding_requests: int = 0
    auth_requests: int = 0
    discovery_requests: int = 0
    total_requests: int = 0
    actual_cost: float = 0.0

    def __post_init__(self) -> None:
        self.limits.validate()

    def before_call(self, kind: CallKind) -> None:
        next_total = self.total_requests + 1
        if next_total > self.limits.max_total_requests:
            raise StageBBudgetExceeded("total provider request budget exceeded")
        current, maximum = self._counter(kind)
        if current + 1 > maximum:
            raise StageBBudgetExceeded(f"{kind.casefold()} request budget exceeded")
        self.total_requests = next_total
        if kind == "AUTH":
            self.auth_requests += 1
        elif kind == "DISCOVERY":
            self.discovery_requests += 1
        elif kind == "GENERATION":
            self.generation_requests += 1
        else:
            self.embedding_requests += 1

    def record_actual_cost(self, value: float | None) -> None:
        if value is None:
            return
        if value < 0:
            raise ValueError("actual cost cannot be negative")
        next_cost = self.actual_cost + value
        maximum = self.limits.max_actual_cost
        if maximum is not None and next_cost > maximum:
            raise StageBBudgetExceeded("actual provider cost budget exceeded")
        self.actual_cost = next_cost

    def _counter(self, kind: CallKind) -> tuple[int, int]:
        if kind == "AUTH":
            return self.auth_requests, self.limits.max_auth_requests
        if kind == "DISCOVERY":
            return self.discovery_requests, self.limits.max_discovery_requests
        if kind == "GENERATION":
            return self.generation_requests, self.limits.max_generation_requests
        return self.embedding_requests, self.limits.max_embedding_requests

    def public_dict(self) -> dict[str, object]:
        return {
            "generation_requests_used": self.generation_requests,
            "embedding_requests_used": self.embedding_requests,
            "auth_requests_used": self.auth_requests,
            "discovery_requests_used": self.discovery_requests,
            "total_requests_used": self.total_requests,
            "actual_cost": self.actual_cost,
        }


def classify_provider_request(request: httpx.Request) -> CallKind:
    path = request.url.path.casefold()
    if path.endswith("/api/v2/oauth"):
        return "AUTH"
    if "embedding" in path:
        return "EMBEDDING"
    if "completion" in path or "chat/completions" in path:
        return "GENERATION"
    return "DISCOVERY"


class BudgetedTransport(httpx.BaseTransport):
    """Count and reject a provider HTTP call before it leaves the process."""

    def __init__(
        self,
        inner: httpx.BaseTransport,
        ledger: StageBBudgetLedger,
        classifier: Callable[[httpx.Request], CallKind] = classify_provider_request,
    ) -> None:
        self._inner = inner
        self._ledger = ledger
        self._classifier = classifier

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self._ledger.before_call(self._classifier(request))
        return self._inner.handle_request(request)

    def close(self) -> None:
        self._inner.close()


@dataclass(frozen=True)
class StageBPlan:
    candidate: StageBCandidate
    budget: StageBBudget
    matrix_hash: str
    matrix_version: str
    credential_state: CredentialState
    tls_ready: bool
    estimated_cost: float | None
    blockers: tuple[str, ...]

    def canonical_payload(self) -> dict[str, object]:
        return {
            "provider": self.candidate.provider,
            "model": self.candidate.model,
            "config_id": self.candidate.config_id,
            "region": self.candidate.region,
            "roles": list(self.candidate.roles),
            "require_embeddings": self.candidate.require_embeddings,
            "matrix_hash": self.matrix_hash,
            "matrix_version": self.matrix_version,
            "credential_state": self.credential_state,
            "tls_ready": self.tls_ready,
            "estimated_cost": self.estimated_cost,
            "budget": self.budget.public_dict(),
            "blockers": list(self.blockers),
        }

    @property
    def plan_hash(self) -> str:
        encoded = json.dumps(
            self.canonical_payload(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def public_plan(self) -> dict[str, object]:
        return {
            "state": "READY_FOR_OWNER_LIVE_AUTHORIZATION"
            if not self.blockers
            else "LIVE_PROMOTION_BLOCKED",
            "plan_hash": self.plan_hash,
            **self.canonical_payload(),
        }


class StageBPreflightService:
    _SECRET_NAMES = {
        "yandex": "yandex_ai_studio_api_key",
        "gigachat": "gigachat_authorization_key",
    }

    def __init__(self, lane: ProviderLaneService, secrets: SecretStore) -> None:
        self._lane = lane
        self._secrets = secrets

    def build_plan(
        self,
        candidate: StageBCandidate,
        budget: StageBBudget,
        *,
        estimated_cost: float | None = None,
        tls_ready: bool = True,
    ) -> StageBPlan:
        budget.validate()
        if estimated_cost is not None and estimated_cost < 0:
            raise ValueError("estimated cost cannot be negative")
        if (
            budget.max_estimated_cost is not None
            and estimated_cost is not None
            and estimated_cost > budget.max_estimated_cost
        ):
            raise StageBBudgetExceeded("estimated provider cost budget exceeded")

        row = self._lane._capability_row(
            provider=candidate.provider,
            model=candidate.model,
            config_id=candidate.config_id,
            region=candidate.region,
        )
        policy = json.loads(str(row["policy_json"]))
        capabilities = json.loads(str(row["capabilities_json"]))
        privacy = json.loads(str(row["privacy_json"]))
        exact = self._exact_capability(candidate)
        blockers: list[str] = []
        if candidate.region != "RU" or not bool(policy["legal"]):
            blockers.append("REGION_NOT_SUPPORTED")
        if not bool(policy["commercial"]):
            blockers.append("COMMERCIAL_PATH_NOT_VERIFIED")
        if not bool(privacy["privacy_ok"]):
            blockers.append("PRIVACY_POLICY_NOT_VERIFIED")
        supported_roles = tuple(str(value) for value in capabilities["roles"])
        if any(role not in supported_roles for role in candidate.roles):
            blockers.append("CAPABILITY_MISSING")
        if not bool(capabilities["generation"]) or not bool(capabilities["structured_output"]):
            blockers.append("CAPABILITY_MISSING")
        if candidate.require_embeddings and not bool(capabilities["embeddings"]):
            blockers.append("CAPABILITY_MISSING")

        credential_state = self._credential_state(candidate.provider)
        if credential_state != "AVAILABLE":
            blockers.append("CREDENTIAL_MISSING")
        if candidate.provider == "gigachat" and not tls_ready:
            blockers.append("TLS_TRUST_NOT_READY")
        if candidate.provider not in self._SECRET_NAMES:
            blockers.append("PROVIDER_NOT_SUPPORTED_FOR_RU_STAGE_B")

        return StageBPlan(
            candidate=candidate,
            budget=budget,
            matrix_hash=str(row["matrix_hash"]),
            matrix_version=exact.matrix_version,
            credential_state=credential_state,
            tls_ready=tls_ready,
            estimated_cost=estimated_cost,
            blockers=tuple(dict.fromkeys(blockers)),
        )

    def revalidate(self, plan: StageBPlan) -> StageBPlan:
        current = self.build_plan(
            plan.candidate,
            plan.budget,
            estimated_cost=plan.estimated_cost,
            tls_ready=plan.tls_ready,
        )
        if current.plan_hash != plan.plan_hash:
            raise StageBPlanMismatch("Stage B preflight is stale; build and authorize a new plan")
        return current

    def _credential_state(self, provider: str) -> CredentialState:
        name = self._SECRET_NAMES.get(provider)
        if name is None:
            return "NOT AVAILABLE"
        try:
            value = self._secrets.get_secret(name)
        except Exception:
            return "NOT AVAILABLE"
        return "AVAILABLE" if value else "NOT AVAILABLE"

    def _exact_capability(self, candidate: StageBCandidate) -> ProviderCapability:
        for item in self._lane.capabilities():
            if (
                item.provider == candidate.provider
                and item.model == candidate.model
                and item.config_id == candidate.config_id
                and item.region == candidate.region
            ):
                return item
        raise StageBGateError("provider capability identity is not current")


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def production_capabilities(
    lane: ProviderLaneService,
    *,
    role: str,
    now: datetime | None = None,
    live_health_ttl: timedelta = timedelta(hours=24),
) -> tuple[ProviderCapability, ...]:
    """Overlay role promotion with LIVE-only, exact-config, fresh health evidence."""

    reference = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    capabilities = lane.capabilities(role=role)
    with lane.engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    "SELECT provider, model, config_id, region, outcome, created_at "
                    "FROM provider_probe_runs WHERE probe_type='LIVE' ORDER BY created_at DESC"
                )
            )
            .mappings()
            .all()
        )

    latest: dict[tuple[str, str, str, str], tuple[str, str]] = {}
    for row in rows:
        identity = (
            str(row["provider"]),
            str(row["model"]),
            str(row["config_id"]),
            str(row["region"]),
        )
        latest.setdefault(identity, (str(row["outcome"]), str(row["created_at"])))

    result: list[ProviderCapability] = []
    for item in capabilities:
        identity = (item.provider, item.model, item.config_id, item.region)
        evidence = latest.get(identity)
        health: HealthState = "UNKNOWN"
        if evidence is not None:
            outcome, created_at = evidence
            timestamp = _parse_timestamp(created_at)
            if timestamp is not None and reference - timestamp <= live_health_ttl:
                health = "HEALTHY" if outcome == "SUCCESS" else "UNAVAILABLE"
        result.append(replace(item, health=health))
    return tuple(result)


def production_route(
    lane: ProviderLaneService,
    *,
    role: str,
    embeddings: bool = False,
    now: datetime | None = None,
    live_health_ttl: timedelta = timedelta(hours=24),
) -> Any:
    candidates = production_capabilities(
        lane, role=role, now=now, live_health_ttl=live_health_ttl
    )
    promoted = tuple(item for item in candidates if item.promotion == "PROMOTED")
    return RussiaPolicy().route(
        promoted if promoted else candidates,
        role=role,
        require_embeddings=embeddings,
    )


def simulate_outage(
    lane: ProviderLaneService,
    *,
    role: str,
    unavailable_provider: str,
    unavailable_model: str,
    unavailable_config_id: str,
    embeddings: bool = False,
    now: datetime | None = None,
) -> Any:
    """In-memory outage simulation; never mutates persisted provider health."""

    candidates = []
    for item in production_capabilities(lane, role=role, now=now):
        if item.promotion != "PROMOTED":
            continue
        if (
            item.provider == unavailable_provider
            and item.model == unavailable_model
            and item.config_id == unavailable_config_id
        ):
            candidates.append(replace(item, health="UNAVAILABLE"))
        else:
            candidates.append(item)
    if not candidates:
        return RussiaPolicy().route(
            production_capabilities(lane, role=role, now=now),
            role=role,
            require_embeddings=embeddings,
        )
    return RussiaPolicy().route(tuple(candidates), role=role, require_embeddings=embeddings)


@dataclass(frozen=True)
class StageBRoleEvidence:
    role: str
    dataset_id: str
    dataset_hash: str
    scorecard_ref: str
    snapshot_id: str
    independence_state: str
    blocking_dimensions: tuple[str, ...]
    missing_dimensions: tuple[str, ...]

    @property
    def promotable(self) -> bool:
        return not self.blocking_dimensions and not self.missing_dimensions

    def public_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "dataset_id": self.dataset_id,
            "dataset_hash": self.dataset_hash,
            "scorecard_ref": self.scorecard_ref,
            "snapshot_id": self.snapshot_id,
            "independence_state": self.independence_state,
            "blocking_dimensions": list(self.blocking_dimensions),
            "missing_dimensions": list(self.missing_dimensions),
            "promotable": self.promotable,
        }


def role_evidence_from_report(
    report: BookBenchReport,
    *,
    role: str,
    dataset_id: str,
    dataset_hash: str,
    scorecard_ref: str,
    required_dimensions: Sequence[str],
    independence_state: str = "UNKNOWN",
    require_independence: bool = False,
) -> StageBRoleEvidence:
    states = {item.dimension: item.state for item in report.dimensions}
    missing = tuple(dimension for dimension in required_dimensions if dimension not in states)
    blocking = tuple(
        dimension
        for dimension in required_dimensions
        if states.get(dimension) == "BLOCKING"
    )
    if require_independence and independence_state != "INDEPENDENT":
        blocking = tuple(dict.fromkeys((*blocking, "EVALUATOR_INDEPENDENCE")))
    return StageBRoleEvidence(
        role=role,
        dataset_id=dataset_id,
        dataset_hash=dataset_hash,
        scorecard_ref=scorecard_ref,
        snapshot_id=report.snapshot_id,
        independence_state=independence_state,
        blocking_dimensions=blocking,
        missing_dimensions=missing,
    )


@dataclass
class StageBProviderRuntime:
    ledger: StageBBudgetLedger
    generation: ModelAdapter
    embedding: EmbeddingAdapter
    client: httpx.Client

    def close(self) -> None:
        self.client.close()


def build_provider_runtime(
    plan: StageBPlan,
    secrets: SecretStore,
    *,
    transport: httpx.BaseTransport | None = None,
    ca_bundle: str | None = None,
) -> StageBProviderRuntime:
    """Build accepted Stage A adapters behind one hard-budget transport."""

    if plan.blockers:
        raise StageBGateError(f"Stage B preflight blocked: {','.join(plan.blockers)}")
    ledger = StageBBudgetLedger(plan.budget)
    if transport is None:
        verify: bool | str = True
        if ca_bundle is not None:
            if not Path(ca_bundle).exists():
                raise StageBGateError("TLS_TRUST_NOT_READY")
            verify = ca_bundle
        inner: httpx.BaseTransport = httpx.HTTPTransport(verify=verify)
    else:
        inner = transport
    client = httpx.Client(transport=BudgetedTransport(inner, ledger))
    provider = plan.candidate.provider
    generation: ModelAdapter
    embedding: EmbeddingAdapter
    if provider == "yandex":
        generation = YandexAdapter(secrets, client=client)
        embedding = YandexEmbeddingAdapter(secrets, client=client)
    elif provider == "gigachat":
        giga = GigaChatAdapter(secrets, client=client)
        generation = giga
        embedding = GigaChatEmbeddingAdapter(giga)
    else:
        client.close()
        raise StageBGateError("provider is not eligible for RU Stage B runtime")
    return StageBProviderRuntime(
        ledger=ledger,
        generation=generation,
        embedding=embedding,
        client=client,
    )


def require_authorized_execution(
    preflight: StageBPreflightService,
    plan: StageBPlan,
    *,
    authorized_plan_hash: str,
) -> None:
    """Owner-gated execution boundary. This function itself makes no provider call."""

    if os.environ.get("BOOK_OS_ALLOW_LIVE_PROVIDER") != "1":
        raise StageBGateError("live provider execution requires BOOK_OS_ALLOW_LIVE_PROVIDER=1")
    if authorized_plan_hash != plan.plan_hash:
        raise StageBPlanMismatch("authorized Stage B plan hash does not match preflight")
    current = preflight.revalidate(plan)
    if current.blockers:
        raise StageBGateError(f"Stage B preflight blocked: {','.join(current.blockers)}")
