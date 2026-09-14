#!/usr/bin/env python3
"""Store and use the dedicated BOOK OS Agents API development key via macOS Keychain.

The secret is never printed, written to the repository, or passed on the command
line. `run` retrieves it only long enough to place it in the child process
environment as BOOK_OS_AGENTS_API_KEY, while removing OPENAI_API_KEY to avoid
accidental production-key aliasing.
"""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys


SERVICE = "book-os.agents-development-api-key"
ACCOUNT = "book-os-development"
SECURITY = "/usr/bin/security"


def _require_macos() -> None:
    if sys.platform != "darwin" or not Path(SECURITY).is_file():
        raise SystemExit("This helper requires macOS Keychain (/usr/bin/security).")


def _security(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    _require_macos()
    return subprocess.run(
        [SECURITY, *args],
        input=input_text,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _read_secret() -> str:
    result = _security(
        "find-generic-password",
        "-a",
        ACCOUNT,
        "-s",
        SERVICE,
        "-w",
    )
    if result.returncode != 0:
        raise SystemExit(
            "Dedicated Agents API development key is not present in macOS Keychain. "
            "Run this helper with `store` after creating the restricted key in the "
            "BOOK-OS-DEVELOPMENT OpenAI Platform project."
        )
    secret = result.stdout.rstrip("\n")
    if not secret:
        raise SystemExit("Keychain returned an empty development key.")
    return secret


def _store_secret() -> int:
    first = getpass.getpass("Paste dedicated BOOK-OS-DEVELOPMENT API key: ").strip()
    if not first:
        raise SystemExit("Refusing to store an empty key.")
    second = getpass.getpass("Paste it again to confirm: ").strip()
    if first != second:
        raise SystemExit("Key confirmation did not match; nothing was stored.")

    result = _security(
        "add-generic-password",
        "-U",
        "-a",
        ACCOUNT,
        "-s",
        SERVICE,
        "-w",
        first,
    )
    if result.returncode != 0:
        raise SystemExit("macOS Keychain refused the development-key update.")
    print(f"Stored dedicated development credential in macOS Keychain service {SERVICE!r}.")
    return 0


def _status() -> int:
    result = _security(
        "find-generic-password",
        "-a",
        ACCOUNT,
        "-s",
        SERVICE,
    )
    present = result.returncode == 0
    print("present" if present else "missing")
    return 0 if present else 1


def _delete() -> int:
    result = _security(
        "delete-generic-password",
        "-a",
        ACCOUNT,
        "-s",
        SERVICE,
    )
    if result.returncode != 0:
        print("missing")
        return 0
    print("deleted local Keychain credential")
    return 0


def _run_agent(agent_args: list[str]) -> int:
    if not agent_args:
        raise SystemExit("`run` requires arguments for safe_development_agent.py")
    secret = _read_secret()
    script = Path(__file__).with_name("safe_development_agent.py")
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env["BOOK_OS_AGENTS_API_KEY"] = secret
    try:
        completed = subprocess.run(
            [sys.executable, str(script), *agent_args],
            env=env,
            check=False,
        )
        return completed.returncode
    finally:
        env.pop("BOOK_OS_AGENTS_API_KEY", None)
        secret = ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("store", help="securely store/replace the dedicated development key")
    subparsers.add_parser("status", help="report whether the Keychain item exists")
    subparsers.add_parser("delete", help="delete only the local Keychain copy")
    run_parser = subparsers.add_parser("run", help="run the isolated Agents API helper")
    run_parser.add_argument("agent_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.command == "store":
        return _store_secret()
    if args.command == "status":
        return _status()
    if args.command == "delete":
        return _delete()
    if args.command == "run":
        return _run_agent(args.agent_args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
