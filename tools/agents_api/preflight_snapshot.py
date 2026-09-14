#!/usr/bin/env python3
"""Validate a BOOK OS Git snapshot before any Agents API call.

This command performs no network or model call. It checks only committed Git
content at an explicit ref/SHA and fails closed on risky credential-bearing
paths, high-risk credential patterns, or an archive above the inline upload
limit used by the initial isolated Agents API lane.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile


INLINE_LIMIT_BYTES = 5 * 1024 * 1024
SENSITIVE_PATH_PATTERNS = (
    re.compile(r"(^|/)\.env(?:\.|$)"),
    re.compile(r"(^|/)(?:id_rsa|id_ed25519)$"),
    re.compile(r"\.(?:pem|p12|pfx|key|mobileprovision)$", re.IGNORECASE),
)
SECRET_CONTENT_PATTERN = re.compile(
    r"(?:sk-proj-[A-Za-z0-9_\-]{16,}|"
    r"github_pat_[A-Za-z0-9_]{20,}|"
    r"gh[pousr]_[A-Za-z0-9]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{20,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"AIza[0-9A-Za-z_\-]{30,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


def _run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _resolve(repo: Path, ref: str) -> str:
    return _run(repo, "rev-parse", f"{ref}^{{commit}}").stdout.strip()


def _tracked_paths(repo: Path, sha: str) -> list[str]:
    output = _run(repo, "ls-tree", "-r", "--name-only", sha).stdout
    return [line for line in output.splitlines() if line]


def _unsafe_paths(repo: Path, sha: str) -> list[str]:
    return [
        path
        for path in _tracked_paths(repo, sha)
        if any(pattern.search(path) for pattern in SENSITIVE_PATH_PATTERNS)
    ]


def _secret_matches(repo: Path, sha: str) -> list[str]:
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
    return result.stdout.splitlines() if result.returncode == 0 else []


def _archive_size(repo: Path, sha: str) -> int:
    with tempfile.TemporaryDirectory(prefix="book-os-agents-preflight-") as tmp:
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
        return archive.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--ref", required=True, help="Explicit Git ref or commit SHA")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"Not a Git checkout: {repo}")

    sha = _resolve(repo, args.ref)
    unsafe = _unsafe_paths(repo, sha)
    secrets = _secret_matches(repo, sha)
    archive_size = _archive_size(repo, sha)

    result = {
        "source_ref": args.ref,
        "source_sha": sha,
        "tracked_sensitive_paths": unsafe,
        "high_risk_secret_matches": secrets,
        "archive_size_bytes": archive_size,
        "inline_limit_bytes": INLINE_LIMIT_BYTES,
        "within_inline_limit": archive_size <= INLINE_LIMIT_BYTES,
        "network_calls": 0,
        "model_calls": 0,
        "status": "PASS",
    }

    failures: list[str] = []
    if unsafe:
        failures.append("tracked credential-bearing path detected")
    if secrets:
        failures.append("high-risk credential pattern detected")
    if archive_size > INLINE_LIMIT_BYTES:
        failures.append("snapshot exceeds initial inline upload limit")

    if failures:
        result["status"] = "BLOCKING"
        result["failures"] = failures

    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
