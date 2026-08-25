from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
from time import perf_counter

from book_os_core.authority import AuthorityService
from book_os_core.backup import create_backup, restore_backup
from book_os_core.db import create_database


def run(entities: int, revisions_per_entity: int) -> dict[str, float | int]:
    with tempfile.TemporaryDirectory(prefix="book-os-m1-bench-") as temporary:
        root = Path(temporary)
        db_path = root / "project.sqlite"
        service = AuthorityService(create_database(db_path))
        heads = []
        acceptance_times: list[float] = []
        for entity_index in range(entities):
            head = service.register_entity(
                entity_type="benchmark.entity",
                payload={"entity": entity_index, "revision": 0, "text": "synthetic"},
                schema_name="benchmark.entity",
                schema_version="1",
                actor="benchmark-owner",
            )
            for revision_index in range(1, revisions_per_entity):
                proposal = service.create_proposal(
                    entity_id=head.entity_id,
                    base_revision_id=head.revision_id,
                    base_revision_hash=head.revision_hash,
                    proposed_payload={
                        "entity": entity_index,
                        "revision": revision_index,
                        "text": "synthetic authority history",
                    },
                    schema_name="benchmark.entity",
                    schema_version="1",
                    rationale="synthetic benchmark",
                    actor="benchmark-owner",
                )
                started = perf_counter()
                service.accept_proposal(
                    proposal,
                    actor="benchmark-owner",
                    actor_kind="HUMAN",
                    reason="synthetic benchmark acceptance",
                    gates={"synthetic": True},
                )
                acceptance_times.append(perf_counter() - started)
                head = service.get_head(head.entity_id)
            heads.append(head)

        lookup_started = perf_counter()
        for head in heads:
            service.get_head(head.entity_id)
        lookup_time = perf_counter() - lookup_started

        backup_started = perf_counter()
        backup_dir = root / "backup"
        create_backup(db_path, backup_dir)
        backup_time = perf_counter() - backup_started

        restore_started = perf_counter()
        restored = root / "restored.sqlite"
        restore_backup(backup_dir, restored)
        restore_time = perf_counter() - restore_started

        total_revisions = entities * revisions_per_entity
        total_proposals = entities * (revisions_per_entity - 1)
        return {
            "entities": entities,
            "revisions": total_revisions,
            "proposals_decisions_approvals": total_proposals,
            "database_bytes": db_path.stat().st_size,
            "authority_lookup_total_seconds": lookup_time,
            "authority_lookup_average_ms": lookup_time / entities * 1000,
            "proposal_acceptance_average_ms": sum(acceptance_times) / len(acceptance_times) * 1000,
            "backup_seconds": backup_time,
            "restore_seconds": restore_time,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entities", type=int, default=100)
    parser.add_argument("--revisions-per-entity", type=int, default=20)
    args = parser.parse_args()
    results = run(args.entities, args.revisions_per_entity)
    for key, value in results.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
