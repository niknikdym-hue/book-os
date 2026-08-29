"""Explicit local CLI for Owner-gated M8 Stage B execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .db import create_database
from .provider_lane import ProviderLaneService
from .secrets import MacOSKeychainSecretStore, SecretStore
from .stage_b import StageBBudget, StageBCandidate, StageBError, StageBPreflightService
from .stage_b_bookbench import execute_writer_bookbench_fixture
from .stage_b_editor import execute_editor_fixture
from .stage_b_judge import execute_independent_judges


def _csv(value: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    if not items:
        raise argparse.ArgumentTypeError("at least one value is required")
    return items


def _add_candidate_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--provider", required=True, choices=("yandex", "gigachat"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--config-id", required=True)
    parser.add_argument("--region", default="RU")
    parser.add_argument("--max-generation", required=True, type=int)
    parser.add_argument("--max-embedding", required=True, type=int)
    parser.add_argument("--max-total", required=True, type=int)
    parser.add_argument("--max-auth", type=int, default=0)
    parser.add_argument("--max-discovery", type=int, default=0)
    parser.add_argument("--max-estimated-cost", type=float)
    parser.add_argument("--max-actual-cost", type=float)
    parser.add_argument("--estimated-cost", type=float)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="book-os-stage-b")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight")
    _add_candidate_args(preflight)
    preflight.add_argument("--roles", required=True, type=_csv)
    preflight.add_argument("--require-embeddings", action="store_true")

    writer = subparsers.add_parser("writer")
    _add_candidate_args(writer)
    writer.add_argument("--authorized-plan-hash", required=True)
    writer.add_argument("--semantic", action="store_true")

    editor = subparsers.add_parser("editor")
    _add_candidate_args(editor)
    editor.add_argument("--source-book-id", required=True)
    editor.add_argument("--authorized-plan-hash", required=True)

    judge = subparsers.add_parser("judge")
    _add_candidate_args(judge)
    judge.add_argument("--book-id", required=True)
    judge.add_argument("--snapshot-id", required=True)
    judge.add_argument("--subject-provider", required=True)
    judge.add_argument("--subject-model", required=True)
    judge.add_argument("--subject-config-id", required=True)
    judge.add_argument("--dimensions", required=True, type=_csv)
    judge.add_argument("--authorized-plan-hash", required=True)
    return parser


def _budget(args: argparse.Namespace) -> StageBBudget:
    return StageBBudget(
        max_generation_requests=args.max_generation,
        max_embedding_requests=args.max_embedding,
        max_total_requests=args.max_total,
        max_auth_requests=args.max_auth,
        max_discovery_requests=args.max_discovery,
        max_estimated_cost=args.max_estimated_cost,
        max_actual_cost=args.max_actual_cost,
    )


def _candidate(
    args: argparse.Namespace, roles: tuple[str, ...], *, embeddings: bool = False
) -> StageBCandidate:
    return StageBCandidate(
        provider=args.provider,
        model=args.model,
        config_id=args.config_id,
        region=args.region,
        roles=roles,
        require_embeddings=embeddings,
    )


def _context(
    args: argparse.Namespace, secrets: SecretStore
) -> tuple[Path, ProviderLaneService, StageBPreflightService]:
    data_dir = Path(args.data_dir).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    lane = ProviderLaneService(create_database(data_dir / "provider-lane.sqlite"))
    return data_dir, lane, StageBPreflightService(lane, secrets)


def _plan(
    args: argparse.Namespace,
    preflight: StageBPreflightService,
    roles: tuple[str, ...],
    *,
    embeddings: bool = False,
):
    return preflight.build_plan(
        _candidate(args, roles, embeddings=embeddings),
        _budget(args),
        estimated_cost=args.estimated_cost,
    )


def run(argv: Sequence[str] | None = None, *, secrets: SecretStore | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    secret_store = secrets or MacOSKeychainSecretStore()
    try:
        data_dir, lane, preflight = _context(args, secret_store)
        if args.command == "preflight":
            plan = _plan(
                args,
                preflight,
                args.roles,
                embeddings=bool(args.require_embeddings),
            )
            print(json.dumps(plan.public_plan(), ensure_ascii=False, sort_keys=True))
            return 0 if not plan.blockers else 3

        if args.command == "writer":
            plan = _plan(args, preflight, ("WRITER",), embeddings=bool(args.semantic))
            evidence = execute_writer_bookbench_fixture(
                data_dir=data_dir,
                preflight=preflight,
                plan=plan,
                authorized_plan_hash=args.authorized_plan_hash,
                lane=lane,
                secrets=secret_store,
                run_semantic=bool(args.semantic),
            )
            print(json.dumps(evidence.public_dict(), ensure_ascii=False, sort_keys=True))
            return 0

        if args.command == "editor":
            plan = _plan(args, preflight, ("EDITOR",))
            evidence = execute_editor_fixture(
                data_dir=data_dir,
                source_book_id=args.source_book_id,
                preflight=preflight,
                plan=plan,
                authorized_plan_hash=args.authorized_plan_hash,
                lane=lane,
                secrets=secret_store,
            )
            print(json.dumps(evidence.public_dict(), ensure_ascii=False, sort_keys=True))
            return 0

        plan = _plan(args, preflight, ("EVALUATOR",))
        evidence = execute_independent_judges(
            data_dir=data_dir,
            book_id=args.book_id,
            snapshot_id=args.snapshot_id,
            subject_identity={
                "provider": args.subject_provider,
                "model": args.subject_model,
                "config_id": args.subject_config_id,
            },
            dimensions=args.dimensions,
            preflight=preflight,
            plan=plan,
            authorized_plan_hash=args.authorized_plan_hash,
            lane=lane,
            secrets=secret_store,
        )
        print(json.dumps(evidence.public_dict(), ensure_ascii=False, sort_keys=True))
        return 0
    except (StageBError, ValueError, RuntimeError) as exc:
        print(
            json.dumps(
                {"status": "BLOCKED", "error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
