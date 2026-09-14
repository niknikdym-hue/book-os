from __future__ import annotations

import json
from typing import Any, cast

from sqlalchemy import text

from .authority import new_ulid
from .authority_types import utc_now
from .series_similarity import semantic_series_findings
from .series_workspace_base import *  # noqa: F401,F403
from .series_workspace_base import (
    SeriesMapView,
    SeriesWorkspaceService as _BaseSeriesWorkspaceService,
)


class SeriesWorkspaceService(_BaseSeriesWorkspaceService):
    """Series workspace with a deterministic semantic/structural anti-clone layer.

    The base workspace owns persistence, rights, lifecycle, exports and exact-overlap checks.
    This extension adds high-confidence semantic findings for paraphrase/domain-substitution cases
    that exact lexical matching cannot catch. It never calls a model or external provider.
    """

    def _semantic_findings(self, series_profile_id: str) -> list[dict[str, Any]]:
        books = self.books(series_profile_id)
        findings: list[dict[str, Any]] = []
        for index, left in enumerate(books):
            left_architecture = self._architecture_material(left.book_id)
            left_sources = (
                [] if left.origin_kind == "LEGACY_TITLE_ONLY" else self._source_rows(left.book_id)
            )
            for right in books[index + 1 :]:
                right_architecture = self._architecture_material(right.book_id)
                right_sources = (
                    []
                    if right.origin_kind == "LEGACY_TITLE_ONLY"
                    else self._source_rows(right.book_id)
                )
                for candidate in semantic_series_findings(
                    left,
                    right,
                    left_architecture=left_architecture,
                    right_architecture=right_architecture,
                    left_sources=left_sources,
                    right_sources=right_sources,
                ):
                    findings.append(
                        {
                            "finding_id": new_ulid(),
                            "book_id": left.book_id,
                            "compared_book_id": right.book_id,
                            "dimension": candidate.dimension,
                            "severity": candidate.severity,
                            "evidence": candidate.evidence,
                        }
                    )
        return findings

    def analyze(self, series_profile_id: str) -> SeriesMapView:
        exact = super().analyze(series_profile_id)
        semantic = self._semantic_findings(series_profile_id)
        if not semantic:
            return exact

        books = self.books(series_profile_id)
        if not books:
            return exact
        anchor = books[0].book_id
        engine = self._engine(anchor)
        now = utc_now()
        persisted: list[dict[str, Any]] = []
        try:
            with engine.begin() as connection:
                existing_signatures = {
                    str(evidence.get("semantic_signature"))
                    for row in connection.execute(
                        text(
                            "SELECT evidence_json FROM series_similarity_findings "
                            "WHERE series_profile_id=:series AND map_hash=:hash"
                        ),
                        {"series": series_profile_id, "hash": exact.map_hash},
                    ).mappings()
                    if isinstance(
                        (evidence := json.loads(str(row["evidence_json"]))),
                        dict,
                    )
                    and evidence.get("semantic_signature")
                }
                for item in semantic:
                    signature = str(item["evidence"].get("semantic_signature", ""))
                    if signature and signature in existing_signatures:
                        continue
                    persisted_evidence = {
                        **cast(dict[str, Any], item["evidence"]),
                        "subject_book_id": item["book_id"],
                        "compared_book_id": item["compared_book_id"],
                    }
                    connection.execute(
                        text(
                            "INSERT INTO series_similarity_findings(finding_id,series_profile_id,"
                            "book_id,compared_book_id,dimension,severity,evidence_json,map_hash,status,"
                            "created_at) VALUES (:id,:series,:book,:compared,:dimension,'BLOCKING',"
                            ":evidence,:hash,'OPEN',:created)"
                        ),
                        {
                            "id": item["finding_id"],
                            "series": series_profile_id,
                            "book": anchor,
                            "compared": item["compared_book_id"],
                            "dimension": item["dimension"],
                            "evidence": json.dumps(
                                persisted_evidence,
                                ensure_ascii=False,
                                sort_keys=True,
                            ),
                            "hash": exact.map_hash,
                            "created": now,
                        },
                    )
                    persisted.append(item)
                    if signature:
                        existing_signatures.add(signature)

                # Even when this exact semantic finding was already persisted, the latest map run
                # must truthfully remain BLOCKING for the same current map hash.
                total_findings = connection.execute(
                    text(
                        "SELECT COUNT(*) FROM series_similarity_findings "
                        "WHERE series_profile_id=:series AND map_hash=:hash"
                    ),
                    {"series": series_profile_id, "hash": exact.map_hash},
                ).scalar_one()
                connection.execute(
                    text(
                        "INSERT INTO series_map_runs(map_run_id,series_profile_id,book_id,map_hash,"
                        "status,finding_count,created_at) VALUES (:id,:series,:book,:hash,'BLOCKING',"
                        ":count,:created)"
                    ),
                    {
                        "id": new_ulid(),
                        "series": series_profile_id,
                        "book": anchor,
                        "hash": exact.map_hash,
                        "count": int(total_findings),
                        "created": now,
                    },
                )
        finally:
            engine.dispose()

        # Return the current persisted view so callers see both exact and semantic findings and so
        # map approval cannot race past the newly persisted BLOCKING run.
        current = self.current_map(series_profile_id)
        if current is None:
            return SeriesMapView(
                map_hash=exact.map_hash,
                status="BLOCKING",
                findings=[*exact.findings, *persisted],
                approved=False,
                current=True,
            )
        return current
