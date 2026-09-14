#!/usr/bin/env python3
"""Recover a preserved BOOK OS Managed Agents session after a streaming disconnect.

This helper never creates a new session or turn. It reads the dedicated development
API key from macOS Keychain, discovers the latest session/turn ids from an existing
events.jsonl, retrieves the canonical turn status, and downloads immutable output
artifacts if that turn completed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Iterable

from openai import OpenAI


SERVICE = "book-os.agents-development-api-key"
ACCOUNT = "book-os-development"
SECURITY = "/usr/bin/security"
MAX_SECRET_BYTES = 16_384
SECRET_OUTPUT_PATTERN = re.compile(
    r"(sk-proj-[A-Za-z0-9_-]{16,}|"
    r"github_pat_[A-Za-z0-9_]{20,}|"
    r"gh[pousr]_[A-Za-z0-9]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{20,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"AIza[0-9A-Za-z_-]{30,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
TERMINAL = {"completed", "failed", "cancelled"}
NONTERMINAL = {"queued", "in_progress", "waiting"}


def _read_key() -> str:
    if sys.platform != "darwin" or not Path(SECURITY).is_file():
        raise SystemExit("This recovery helper requires macOS Keychain.")
    result = subprocess.run(
        [
            SECURITY,
            "find-generic-password",
            "-a",
            ACCOUNT,
            "-s",
            SERVICE,
            "-w",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise SystemExit("Dedicated BOOK OS Agents API development key is missing from Keychain.")
    secret = result.stdout.rstrip("\n")
    if not secret:
        raise SystemExit("Keychain returned an empty development key.")
    if len(secret.encode("utf-8")) > MAX_SECRET_BYTES:
        raise SystemExit("Keychain development credential is unexpectedly large.")
    return secret


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            if isinstance(item, str):
                yield item
            else:
                yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item
            else:
                yield from _walk_strings(item)


def _latest_ids(events_path: Path) -> tuple[str, str]:
    if not events_path.is_file():
        raise SystemExit(f"events.jsonl not found: {events_path}")
    session_id: str | None = None
    turn_id: str | None = None
    with events_path.open("r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {events_path} line {lineno}: {exc}") from exc
            for value in _walk_strings(payload):
                if value.startswith("sess_"):
                    session_id = value
                elif value.startswith("turn_"):
                    turn_id = value
    if not session_id or not turn_id:
        raise SystemExit("Could not recover session_id and turn_id from events.jsonl.")
    return session_id, turn_id


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "to_dict"):
        return value.to_dict()
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _download_artifacts(client: OpenAI, session_id: str, destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    for artifact in client.beta.agents.sessions.artifacts.list(session_id):
        path = str(artifact.path)
        if not path.startswith("/workspace/outputs/"):
            continue
        filename = Path(path).name
        if not filename:
            continue
        response = client.beta.agents.sessions.artifacts.content(
            artifact.id,
            session_id=session_id,
        )
        target = destination / filename
        target.write_bytes(response.read())
        names.append(filename)
    return sorted(set(names))


def _guard_outputs(destination: Path, filenames: list[str]) -> None:
    bad: list[str] = []
    for filename in filenames:
        path = destination / filename
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="ignore")
        if SECRET_OUTPUT_PATTERN.search(text):
            bad.append(filename)
    if bad:
        raise SystemExit(
            "Recovered artifact(s) match a high-risk credential pattern: "
            + ", ".join(sorted(bad))
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/tmp/book-os-t00-t01-result"),
        help="Existing run output directory containing events.jsonl",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=0,
        help="Optionally poll the existing turn for up to this many seconds. No new turn is created.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Polling interval used only with --wait-seconds",
    )
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    events_path = out_dir / "events.jsonl"
    session_id, turn_id = _latest_ids(events_path)
    key = _read_key()

    try:
        with OpenAI(api_key=key) as client:
            deadline = time.monotonic() + max(0, args.wait_seconds)
            last_status: str | None = None
            while True:
                session = client.beta.agents.sessions.retrieve(session_id)
                turn = client.beta.agents.sessions.turns.retrieve(
                    turn_id,
                    session_id=session_id,
                )
                status = str(turn.status)
                if status != last_status:
                    print(f"SESSION {session_id}: {session.status}")
                    print(f"TURN {turn_id}: {status}")
                    last_status = status

                if status in TERMINAL:
                    break
                if status not in NONTERMINAL:
                    print(f"Unknown turn status: {status}")
                    return 3
                if args.wait_seconds <= 0 or time.monotonic() >= deadline:
                    print("Turn is still active. Session preserved; no new turn was created.")
                    return 3
                time.sleep(max(1, args.poll_interval))

            metadata = {
                "session_id": session_id,
                "session_status": str(session.status),
                "session_error": _jsonable(getattr(session, "error", None)),
                "session_usage": _jsonable(getattr(session, "usage", None)),
                "turn_id": turn_id,
                "turn_status": str(turn.status),
                "turn_error": _jsonable(getattr(turn, "error", None)),
                "turn_usage": _jsonable(getattr(turn, "usage", None)),
                "recovered_from_events": str(events_path),
                "created_new_session": False,
                "created_new_turn": False,
            }

            if status != "completed":
                (out_dir / "recovery-metadata.json").write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                print("Turn reached a terminal non-completed state. Session preserved.")
                return 2

            artifacts = _download_artifacts(client, session_id, out_dir)
            _guard_outputs(out_dir, artifacts)
            metadata["artifacts"] = artifacts
            (out_dir / "recovery-metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            required = {"report.md", "book-os.patch", "result.zip"}
            missing = sorted(required - set(artifacts))
            print("ARTIFACTS:", ", ".join(artifacts) if artifacts else "NONE")
            if missing:
                print("Missing required artifacts:", ", ".join(missing))
                print("Session preserved; do not rerun the engineering task yet.")
                return 2

            print("RECOVERY COMPLETE")
            print(out_dir)
            return 0
    finally:
        key = ""


if __name__ == "__main__":
    raise SystemExit(main())
