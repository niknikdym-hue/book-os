from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from typing import Literal, TypeAlias
import unicodedata

JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
AuthorityStatus: TypeAlias = Literal[
    "DRAFT", "PROPOSED", "REVIEWED", "APPROVED", "LOCKED", "SUPERSEDED"
]
ActorKind: TypeAlias = Literal["HUMAN", "SYSTEM", "AI"]
ProvenanceOrigin: TypeAlias = Literal[
    "HUMAN_WRITTEN", "AI_ASSISTED", "AI_GENERATED", "IMPORTED", "SYSTEM_DERIVED"
]

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


class AuthorityError(RuntimeError):
    pass


class StaleBaselineError(AuthorityError):
    pass


class ProposalStateError(AuthorityError):
    pass


class HumanApprovalRequired(AuthorityError):
    pass


class InvalidAuthorityOperation(AuthorityError):
    pass


@dataclass(frozen=True)
class AuthorityHead:
    entity_id: str
    revision_id: str
    revision_hash: str
    status: str


@dataclass(frozen=True)
class ProposalAcceptance:
    proposal_id: str
    revision_id: str
    decision_id: str
    approval_id: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def new_ulid() -> str:
    """Generate a sortable 26-character ULID-style identifier without a runtime dependency."""
    milliseconds = int(datetime.now(timezone.utc).timestamp() * 1000)
    value = (milliseconds << 80) | int.from_bytes(os.urandom(10), "big")
    chars = ["0"] * 26
    for index in range(25, -1, -1):
        chars[index] = _CROCKFORD[value & 31]
        value >>= 5
    return "".join(chars)


def _normalize_json(value: JSONValue) -> JSONValue:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalize_json(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, JSONValue] = {}
        for key, item in value.items():
            normalized[unicodedata.normalize("NFC", key)] = _normalize_json(item)
        return normalized
    return value


def canonical_json(payload: Mapping[str, JSONValue]) -> str:
    normalized = _normalize_json(dict(payload))
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def content_hash(payload: Mapping[str, JSONValue]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
