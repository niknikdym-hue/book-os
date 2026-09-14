#!/usr/bin/env python3
"""Run a BOOK OS engineering task in an isolated OpenAI-hosted Agents API sandbox.

Security properties:
- snapshots committed Git content only via `git archive`;
- never copies the working tree, .git, Keychain, BOOK_OS_DATA_DIR, or local credentials;
- keeps the application API key outside the agent sandbox;
- disables sandbox network access;
- gives the agent no GitHub credentials and no push/merge capability;
- retrieves only immutable output artifacts produced under /workspace/outputs.

This is an engineering helper. It is not part of BOOK OS book-writing ModelGateway.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable

from openai import OpenAI


INLINE_LIMIT_BYTES = 5 * 1024 * 1024
DEFAULT_MODEL = "gpt-5.6-sol"
SENSITIVE_PATH_PATTERNS = (
    re.compile(r"(^|/)\.env(?:\.|$)"),
    re.compile(r"(^|/)(?:id_rsa|id_ed25519)$"),
    re.compile(r"\.(?:pem|p12|pfx|key|mobileprovision)$", re.IGNORECASE),
)
SECRET_CONTENT_PATTERN = re.compile(
    r"(?:sk-proj-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


def _git(repo: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=text,
    )


def _resolve_snapshot(repo: Path, ref: str) -> str:
    return _git(repo, "rev-parse", f"{ref}^{{commit}}").stdout.strip()


def _tracked_paths(repo: Path, sha: str) -> list[str]:
    output = _git(repo, "ls-tree", "-r", "--name-only", sha).stdout
    return [line for line in output.splitlines() if line]


def _guard_snapshot(repo: Path, sha: str) -> None:
    unsafe_paths = [
        path
        for path in _tracked_paths(repo, sha)
        if any(pattern.search(path) for pattern in SENSITIVE_PATH_PATTERNS)
    ]
    if unsafe_paths:
        raise SystemExit(
            "Refusing to snapshot potentially credential-bearing tracked paths:\n"
            + "\n".join(f"- {path}" for path in unsafe_paths[:20])
        )

    # Search only committed text at the exact SHA. Exit 1 means no matches.
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "grep",
            "-I",
            "-n",
            "-E",
            SECRET_CONTENT_PATTERN.pattern,
            sha,
            "--",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, 1}:
        raise SystemExit(f"git secret preflight failed: {result.stderr.strip()}")
    if result.returncode == 0 and result.stdout.strip():
        raise SystemExit(
            "Refusing to snapshot: a tracked file matches a high-risk credential pattern.\n"
            + result.stdout[:4000]
        )


def _build_archive(repo: Path, sha: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="book-os-agents-") as tmp:
        archive = Path(tmp) / "book-os-source.tar.gz"
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "archive",
                "--format=tar.gz",
                "--prefix=book-os/",
                "-o",
                str(archive),
                sha,
            ],
            check=True,
        )
        payload = archive.read_bytes()
    if len(payload) > INLINE_LIMIT_BYTES:
        raise SystemExit(
            f"Snapshot is {len(payload)} bytes, above the 5 MiB inline Agents API limit. "
            "Use a smaller task-scoped ref/snapshot or a separately reviewed Files API lane; "
            "do not silently grant broader permissions."
        )
    return payload


def _load_task(args: argparse.Namespace) -> str:
    if args.task and args.task_file:
        raise SystemExit("Use either --task or --task-file, not both")
    if args.task_file:
        return Path(args.task_file).read_text(encoding="utf-8").strip()
    if args.task:
        return args.task.strip()
    raise SystemExit("A task is required via --task or --task-file")


def _walk_ids(value: Any) -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str):
                yield key, item
            yield from _walk_ids(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_ids(item)


def _event_json(event: Any) -> dict[str, Any]:
    if hasattr(event, "to_json"):
        return json.loads(event.to_json(indent=None))
    if hasattr(event, "model_dump"):
        return event.model_dump(mode="json")
    raise TypeError(f"Unsupported Agents API event type: {type(event)!r}")


def _event_type(payload: dict[str, Any]) -> str:
    value = payload.get("type")
    return str(value) if value is not None else ""


def _find_prefixed_id(payload: dict[str, Any], prefix: str) -> str | None:
    for _key, value in _walk_ids(payload):
        if value.startswith(prefix):
            return value
    return None


def _download_artifacts(client: OpenAI, session_id: str, destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] = []
    for artifact in client.beta.agents.sessions.artifacts.list(session_id):
        path = str(artifact.path)
        filename = Path(path).name
        if not filename:
            continue
        target = destination / filename
        with client.beta.agents.sessions.artifacts.with_streaming_response.content(
            artifact.id, session_id=session_id
        ) as response:
            response.stream_to_file(target)
        downloaded.append(filename)
    return downloaded


def _agent_instructions(snapshot_sha: str) -> str:
    return f"""You are the isolated BOOK OS engineering agent.

SOURCE SNAPSHOT SHA: {snapshot_sha}
WORKSPACE: /workspace/book-os

Hard rules:
1. Work only inside /workspace/book-os and /workspace/outputs.
2. There is intentionally no network access. Do not attempt to bypass that restriction.
3. Do not request or search for credentials, API keys, Keychain data, user home files, manuscripts, or BOOK_OS_DATA_DIR.
4. Do not add Git remotes. Do not push, merge, deploy, release, sign, notarize, or replace an installed application.
5. Do not generate a production manuscript or make provider/model calls from BOOK OS itself.
6. Preserve BOOK OS authority and quality gates unless the task explicitly and safely requires a reviewed change.
7. Treat the supplied Git snapshot as the complete authorized code input for this turn.
8. Run the tests/checks that are possible and relevant. Report commands and actual outcomes; never claim a test passed if it did not run.
9. Before finishing, always create:
   - /workspace/outputs/report.md
   - /workspace/outputs/book-os.patch using `git diff --binary HEAD`
   - /workspace/outputs/result.zip containing report.md, book-os.patch, and any concise test log you produced.
10. If no code change is required, still produce an empty patch and explain why in report.md.

The output patch is only a proposal. A separate trusted controller decides whether it may be applied to GitHub.
"""


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--ref", default="main", help="Explicit Git ref/SHA to snapshot")
    parser.add_argument("--task")
    parser.add_argument("--task-file")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out-dir", type=Path, default=Path("agents-api-output"))
    parser.add_argument("--keep-session", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"Not a Git checkout: {repo}")

    api_key = os.environ.get("BOOK_OS_AGENTS_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "BOOK_OS_AGENTS_API_KEY is required. Do not reuse the production BOOK OS key."
        )
    if os.environ.get("OPENAI_API_KEY") == api_key:
        raise SystemExit(
            "Safety stop: the dedicated development key must not be aliased to OPENAI_API_KEY."
        )

    task = _load_task(args)
    sha = _resolve_snapshot(repo, args.ref)
    _guard_snapshot(repo, sha)
    archive = _build_archive(repo, sha)

    encoded = base64.b64encode(archive).decode("ascii")
    environment = {
        "type": "openai_hosted",
        "network": {"access": "disabled"},
        "files": [
            {
                "type": "inline",
                "path": "/workspace/book-os-source.tar.gz",
                "data": encoded,
            }
        ],
        "setup_commands": [
            {"command": "mkdir -p /workspace/outputs"},
            {"command": "tar -xzf /workspace/book-os-source.tar.gz -C /workspace"},
            {
                "command": (
                    "git init -q && git config user.name 'BOOK OS isolated agent' "
                    "&& git config user.email 'agent@invalid' && git add -A "
                    "&& git commit -qm 'authorized snapshot baseline'"
                ),
                "cwd": "/workspace/book-os",
            },
        ],
    }

    session_id: str | None = None
    completed = False
    last_turn_id: str | None = None
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    event_log = out_dir / "events.jsonl"

    with OpenAI(api_key=api_key) as client:
        with client.beta.agents.sessions.create(
            agent={
                "model": args.model,
                "instructions": _agent_instructions(sha),
            },
            environment=environment,
            input=task,
            stream=True,
        ) as events, event_log.open("w", encoding="utf-8") as log:
            for event in events:
                payload = _event_json(event)
                log.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
                log.flush()
                session_id = session_id or _find_prefixed_id(payload, "sess_")
                candidate_turn = _find_prefixed_id(payload, "turn_")
                if candidate_turn:
                    last_turn_id = candidate_turn
                event_type = _event_type(payload)
                if event_type == "agent.session.turn.completed":
                    completed = True
                if event_type in {
                    "agent.session.turn.failed",
                    "agent.session.turn.cancelled",
                    "agent.session.failed",
                }:
                    completed = False

        if session_id is None:
            raise SystemExit("Agents API did not expose a session id; inspect events.jsonl")

        downloaded = _download_artifacts(client, session_id, out_dir)
        metadata = {
            "session_id": session_id,
            "turn_id": last_turn_id,
            "source_sha": sha,
            "source_ref": args.ref,
            "model": args.model,
            "network_access": "disabled",
            "github_credentials_in_sandbox": False,
            "book_os_data_dir_in_sandbox": False,
            "completed_turn_seen": completed,
            "artifacts": downloaded,
        }
        (out_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

        if not args.keep_session:
            client.beta.agents.sessions.delete(session_id)

    required = {"report.md", "book-os.patch", "result.zip"}
    missing = sorted(required - set(downloaded))
    if missing:
        print(f"Missing required artifacts: {', '.join(missing)}", file=sys.stderr)
        return 2
    if not completed:
        print("No completed-turn event observed; inspect events.jsonl and report.md", file=sys.stderr)
        return 3

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
