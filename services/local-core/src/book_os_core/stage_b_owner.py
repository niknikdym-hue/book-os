"""Owner-only M8 Stage B promotion and fallback operations.

This module never calls a provider. It is intentionally separate from the live
execution CLI so evidence generation cannot promote itself.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Sequence

from .db import create_database
from .provider_lane import ProviderLaneService
from .stage_b import StageBGateError, simulate_outage

_PROMOTION_FLAG = "BOOK_OS_ALLOW_PROVIDER_PROMOTION"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="book-os-stage-b-owner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    promote = subparsers.add_parser("promote")
    promote.add_argument("--data-dir", required=True)
    promote.add_argument("--provider", required=True, choices=("yandex", "gigachat"))
    promote.add_argument("--model", required=True, help="Policy/capability model identity")
    promote.add_argument("--config-id", required=True)
    promote.add_argument("--region", default="RU")
    promote.add_argument("--role", required=True, choices=("WRITER", "EDITOR", "EVALUATOR"))
    promote.add_argument("--dataset-hash", required=True)
    promote.add_argument("--dataset-snapshot-id")
    promote.add_argument("--scorecard-ref", required=True)
    promote.add_argument("--reason", required=True)
    promote.add_argument("--actor", required=True)
    promote.add_argument(
        "--independence-state",
        choices=("INDEPENDENT", "SAME_CONFIG", "UNKNOWN"),
        default="UNKNOWN",
    )
    promote.add_argument("--quality-floor-passed", action="store_true")
    promote.add_argument("--confirm-owner-promotion", action="store_true")

    fallback = subparsers.add_parser("fallback")
    fallback.add_argument("--data-dir", required=True)
    fallback.add_argument("--role", required=True, choices=("WRITER", "EDITOR", "EVALUATOR"))
    fallback.add_argument("--unavailable-provider", required=True)
    fallback.add_argument("--unavailable-model", required=True)
    fallback.add_argument("--unavailable-config-id", required=True)
    fallback.add_argument("--embeddings", action="store_true")
    return parser


def _lane(raw_data_dir: str) -> ProviderLaneService:
    data_dir = Path(raw_data_dir).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    return ProviderLaneService(create_database(data_dir / "provider-lane.sqlite"))


def _promotion_allowed(args: argparse.Namespace) -> None:
    if os.environ.get(_PROMOTION_FLAG) != "1":
        raise StageBGateError(f"provider promotion requires {_PROMOTION_FLAG}=1")
    if not args.confirm_owner_promotion:
        raise StageBGateError("provider promotion requires --confirm-owner-promotion")
    if not args.quality_floor_passed:
        raise StageBGateError("provider promotion requires an explicit passed quality floor")


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        lane = _lane(args.data_dir)
        if args.command == "promote":
            _promotion_allowed(args)
            promotion_id = lane.record_promotion(
                provider=args.provider,
                model=args.model,
                config_id=args.config_id,
                region=args.region,
                role=args.role,
                decision="PROMOTED",
                dataset_snapshot_id=args.dataset_snapshot_id,
                dataset_hash=args.dataset_hash,
                scorecard_ref=args.scorecard_ref,
                quality_floor_passed=True,
                reason=args.reason,
                actor=args.actor,
                independence_state=args.independence_state,
            )
            print(
                json.dumps(
                    {
                        "status": "PROMOTED",
                        "promotion_id": promotion_id,
                        "provider": args.provider,
                        "model": args.model,
                        "config_id": args.config_id,
                        "region": args.region,
                        "role": args.role,
                    },
                    sort_keys=True,
                )
            )
            return 0

        decision = simulate_outage(
            lane,
            role=args.role,
            unavailable_provider=args.unavailable_provider,
            unavailable_model=args.unavailable_model,
            unavailable_config_id=args.unavailable_config_id,
            embeddings=bool(args.embeddings),
        )
        print(
            json.dumps(
                {
                    "available": decision.available,
                    "reason": decision.reason,
                    "provider": decision.capability.provider if decision.capability else None,
                    "model": decision.capability.model if decision.capability else None,
                    "config_id": decision.capability.config_id if decision.capability else None,
                    "attempts": [attempt.__dict__.copy() for attempt in decision.attempts],
                },
                sort_keys=True,
            )
        )
        return 0
    except (StageBGateError, ValueError, RuntimeError) as exc:
        print(
            json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
