from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Literal, TypeAlias

from .authority_types import (
    ActorKind,
    AuthorityStatus,
    HumanApprovalRequired,
    InvalidAuthorityOperation,
    JSONValue,
    canonical_json,
    content_hash,
    new_ulid,
)

MysteryAuthorityKind: TypeAlias = Literal[
    "STORY_DEFINITION",
    "NARRATIVE_CONTRACT",
    "CASE_SOLUTION",
    "REALISM_PLAN",
    "MYSTIC_RULE_SET",
    "CHARACTER_BIBLE",
    "CLUE_LEDGER",
    "CASE_TIMELINE",
    "REVEAL_PLAN",
    "SCENE_CONTRACT",
    "REPRESENTATIVE_SAMPLE",
    "PROFESSIONAL_BENCHMARK",
    "EDITORIAL_GATE_STATE",
]

_ACCEPTED_STATUSES: frozenset[AuthorityStatus] = frozenset(("APPROVED", "LOCKED"))
_FROZEN_DEPENDENCY_STATUSES: frozenset[AuthorityStatus] = frozenset(
    ("APPROVED", "LOCKED", "SUPERSEDED")
)

_ALLOWED_TRANSITIONS: dict[AuthorityStatus, frozenset[AuthorityStatus]] = {
    "DRAFT": frozenset(("PROPOSED",)),
    "PROPOSED": frozenset(("REVIEWED", "DRAFT")),
    "REVIEWED": frozenset(("APPROVED", "DRAFT")),
    "APPROVED": frozenset(("LOCKED", "SUPERSEDED")),
    "LOCKED": frozenset(("SUPERSEDED",)),
    "SUPERSEDED": frozenset(),
}


@dataclass(frozen=True)
class MysteryAuthorityRevision:
    """Immutable envelope for one version of a fiction authority object.

    Payload is stored as canonical JSON text so callers cannot mutate an accepted
    revision through a retained dict/list reference. The content hash is therefore
    stable and can be used as exact downstream authority identity.
    """

    entity_id: str
    kind: MysteryAuthorityKind
    revision_id: str
    revision_hash: str
    status: AuthorityStatus
    content_json: str
    supersedes_revision_id: str | None = None

    @property
    def revision_ref(self) -> str:
        return f"{self.entity_id}@{self.revision_id}:{self.revision_hash}"


@dataclass(frozen=True)
class AuthorityDependency:
    """Exact upstream revision consumed by one exact dependent revision."""

    dependent_entity_id: str
    dependent_revision_id: str
    upstream_entity_id: str
    upstream_revision_id: str
    reason: str


@dataclass(frozen=True)
class AuthorityRequirement:
    entity_id: str
    allowed_statuses: frozenset[AuthorityStatus] = _ACCEPTED_STATUSES


@dataclass(frozen=True)
class WritingAdmission:
    allowed: bool
    blocking_reasons: tuple[str, ...]
    authority_revision_refs: tuple[str, ...]


def create_authority_revision(
    *,
    entity_id: str,
    kind: MysteryAuthorityKind,
    payload: Mapping[str, JSONValue],
    status: AuthorityStatus = "DRAFT",
    supersedes_revision_id: str | None = None,
) -> MysteryAuthorityRevision:
    """Create an immutable, content-addressed authority revision."""
    if not entity_id.strip():
        raise InvalidAuthorityOperation("entity_id must not be empty")
    if status in {"APPROVED", "LOCKED"}:
        raise HumanApprovalRequired(
            "new authority content cannot be created directly as APPROVED/LOCKED; "
            "create DRAFT and pass the human transition gate"
        )
    if status == "SUPERSEDED":
        raise InvalidAuthorityOperation("new authority content cannot start SUPERSEDED")
    return MysteryAuthorityRevision(
        entity_id=entity_id,
        kind=kind,
        revision_id=new_ulid(),
        revision_hash=content_hash(payload),
        status=status,
        content_json=canonical_json(payload),
        supersedes_revision_id=supersedes_revision_id,
    )


def revise_authority(
    previous: MysteryAuthorityRevision,
    payload: Mapping[str, JSONValue],
) -> MysteryAuthorityRevision:
    """Create a new DRAFT; never mutate or replace accepted content in place."""
    return create_authority_revision(
        entity_id=previous.entity_id,
        kind=previous.kind,
        payload=payload,
        status="DRAFT",
        supersedes_revision_id=previous.revision_id,
    )


def transition_authority_status(
    revision: MysteryAuthorityRevision,
    *,
    target_status: AuthorityStatus,
    actor_kind: ActorKind,
) -> MysteryAuthorityRevision:
    """Apply an authority-state transition without changing content identity."""
    if target_status == revision.status:
        return revision
    allowed = _ALLOWED_TRANSITIONS[revision.status]
    if target_status not in allowed:
        raise InvalidAuthorityOperation(
            f"invalid authority transition {revision.status} -> {target_status}"
        )
    if target_status in {"APPROVED", "LOCKED"} and actor_kind != "HUMAN":
        raise HumanApprovalRequired(f"{target_status} requires HUMAN authority, got {actor_kind}")
    if target_status == "SUPERSEDED" and actor_kind == "AI":
        raise HumanApprovalRequired("AI cannot supersede accepted authority")
    return replace(revision, status=target_status)


class MysteryAuthorityGraph:
    """In-memory exact-revision dependency and staleness model.

    MYS-01 intentionally has no database concerns. Persistence may later project
    these semantics onto BOOK OS revision storage without changing the rules.
    """

    def __init__(self) -> None:
        self._heads: dict[str, MysteryAuthorityRevision] = {}
        self._bindings_by_revision: dict[tuple[str, str], tuple[AuthorityDependency, ...]] = {}

    def register_head(self, revision: MysteryAuthorityRevision) -> None:
        current = self._heads.get(revision.entity_id)
        if current is not None and current.kind != revision.kind:
            raise InvalidAuthorityOperation(
                f"entity {revision.entity_id} changed kind {current.kind} -> {revision.kind}"
            )

        if (
            current is not None
            and revision.revision_id != current.revision_id
            and revision.supersedes_revision_id == current.revision_id
        ):
            old_key = (current.entity_id, current.revision_id)
            new_key = (revision.entity_id, revision.revision_id)
            if new_key not in self._bindings_by_revision:
                inherited = tuple(
                    replace(item, dependent_revision_id=revision.revision_id)
                    for item in self._bindings_by_revision.get(old_key, ())
                )
                self._bindings_by_revision[new_key] = inherited

        self._heads[revision.entity_id] = revision

    def head(self, entity_id: str) -> MysteryAuthorityRevision | None:
        return self._heads.get(entity_id)

    def heads(self) -> tuple[MysteryAuthorityRevision, ...]:
        return tuple(self._heads.values())

    def _current_dependencies(self, entity_id: str) -> tuple[AuthorityDependency, ...]:
        head = self._heads.get(entity_id)
        if head is None:
            return ()
        return self._bindings_by_revision.get((entity_id, head.revision_id), ())

    def _depends_on(self, start_entity_id: str, target_entity_id: str) -> bool:
        """Return whether current `start` transitively depends on `target`."""
        pending: list[str] = [start_entity_id]
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            for binding in self._current_dependencies(current):
                upstream = binding.upstream_entity_id
                if upstream == target_entity_id:
                    return True
                pending.append(upstream)
        return False

    def bind_dependency(
        self,
        *,
        dependent_entity_id: str,
        upstream_entity_id: str,
        reason: str,
    ) -> AuthorityDependency:
        dependent = self._heads.get(dependent_entity_id)
        upstream = self._heads.get(upstream_entity_id)
        if dependent is None:
            raise InvalidAuthorityOperation(
                f"cannot bind dependency: missing dependent head {dependent_entity_id}"
            )
        if upstream is None:
            raise InvalidAuthorityOperation(
                f"cannot bind dependency: missing upstream head {upstream_entity_id}"
            )
        if dependent_entity_id == upstream_entity_id:
            raise InvalidAuthorityOperation("authority entity cannot depend on itself")

        key = (dependent.entity_id, dependent.revision_id)
        existing = self._bindings_by_revision.get(key, ())
        same_upstream = next(
            (item for item in existing if item.upstream_entity_id == upstream_entity_id),
            None,
        )
        if same_upstream is not None and same_upstream.upstream_revision_id == upstream.revision_id:
            return same_upstream

        if dependent.status in _FROZEN_DEPENDENCY_STATUSES:
            raise InvalidAuthorityOperation(
                "accepted/superseded authority dependencies are immutable; create a new "
                "dependent revision before adding or rebinding dependencies"
            )

        if self._depends_on(upstream_entity_id, dependent_entity_id):
            raise InvalidAuthorityOperation(
                f"dependency cycle rejected: {dependent_entity_id} -> {upstream_entity_id}"
            )

        binding = AuthorityDependency(
            dependent_entity_id=dependent_entity_id,
            dependent_revision_id=dependent.revision_id,
            upstream_entity_id=upstream_entity_id,
            upstream_revision_id=upstream.revision_id,
            reason=reason,
        )
        without_same_upstream = tuple(
            item for item in existing if item.upstream_entity_id != upstream_entity_id
        )
        self._bindings_by_revision[key] = (*without_same_upstream, binding)
        return binding

    def dependencies_for(self, entity_id: str) -> tuple[AuthorityDependency, ...]:
        return self._current_dependencies(entity_id)

    def stale_entities(self) -> frozenset[str]:
        """Return current heads stale from missing/moved exact upstream revisions.

        Staleness is transitive: if B consumes stale A, then everything consuming B
        is stale even if B's own direct upstream revision IDs still exist.
        """
        reverse_edges: dict[str, set[str]] = defaultdict(set)
        stale: set[str] = set()

        for dependent_id, dependent_head in self._heads.items():
            bindings = self._bindings_by_revision.get(
                (dependent_id, dependent_head.revision_id), ()
            )
            for binding in bindings:
                reverse_edges[binding.upstream_entity_id].add(dependent_id)
                upstream = self._heads.get(binding.upstream_entity_id)
                if upstream is None or upstream.revision_id != binding.upstream_revision_id:
                    stale.add(dependent_id)

        queue: deque[str] = deque(stale)
        while queue:
            stale_upstream = queue.popleft()
            for dependent in reverse_edges.get(stale_upstream, set()):
                if dependent not in stale:
                    stale.add(dependent)
                    queue.append(dependent)

        return frozenset(stale)

    def is_fresh(self, entity_id: str) -> bool:
        return entity_id in self._heads and entity_id not in self.stale_entities()


def evaluate_writing_admission(
    graph: MysteryAuthorityGraph,
    requirements: Sequence[AuthorityRequirement],
) -> WritingAdmission:
    """Fail closed unless all required exact authorities exist, are accepted and fresh."""
    stale = graph.stale_entities()
    blockers: list[str] = []
    refs: list[str] = []

    for requirement in requirements:
        head = graph.head(requirement.entity_id)
        if head is None:
            blockers.append(f"MISSING_AUTHORITY:{requirement.entity_id}")
            continue
        refs.append(head.revision_ref)
        if head.status not in requirement.allowed_statuses:
            blockers.append(f"UNACCEPTED_AUTHORITY:{requirement.entity_id}:{head.status}")
        if requirement.entity_id in stale:
            blockers.append(f"STALE_AUTHORITY:{requirement.entity_id}")

    return WritingAdmission(
        allowed=not blockers,
        blocking_reasons=tuple(blockers),
        authority_revision_refs=tuple(refs),
    )


def requirements_for_entities(entity_ids: Iterable[str]) -> tuple[AuthorityRequirement, ...]:
    """Convenience helper for the common APPROVED/LOCKED writing gate."""
    return tuple(AuthorityRequirement(entity_id=entity_id) for entity_id in entity_ids)


def accepted_statuses() -> frozenset[AuthorityStatus]:
    """Return the immutable accepted-status set used by default admission policy."""
    return _ACCEPTED_STATUSES
