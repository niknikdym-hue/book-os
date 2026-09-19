#!/usr/bin/env python3
"""Store and use the dedicated BOOK OS Agents API development key via macOS Keychain.

`store` lets macOS Keychain prompt for the secret itself, so the raw key is not
placed in this helper's argv or shell history. `run` retrieves the key into this
trusted launcher process and passes it to safe_development_agent.py through a
one-shot inherited file descriptor. The raw key is not placed in the child
process environment or command line.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


SERVICE = "book-os.agents-development-api-key"
ACCOUNT = "book-os-development"
SECURITY = "/usr/bin/security"
MAX_SECRET_BYTES = 16_384


def _require_macos() -> None:
    if sys.platform != "darwin" or not Path(SECURITY).is_file():
        raise SystemExit("This helper requires macOS Keychain (/usr/bin/security).")


def _security_capture(*args: str) -> subprocess.CompletedProcess[str]:
    _require_macos()
    return subprocess.run(
        [SECURITY, *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _read_secret() -> str:
    result = _security_capture(
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
    if len(secret.encode("utf-8")) > MAX_SECRET_BYTES:
        raise SystemExit("Keychain development credential is unexpectedly large.")
    return secret


def _store_secret() -> int:
    _require_macos()
    print(
        "macOS Keychain will securely prompt for the dedicated BOOK-OS-DEVELOPMENT API key. "
        "The secret will not be passed on this command line."
    )
    result = subprocess.run(
        [
            SECURITY,
            "add-generic-password",
            "-U",
            "-a",
            ACCOUNT,
            "-s",
            SERVICE,
            "-w",
        ],
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        raise SystemExit("macOS Keychain refused the development-key update.")
    print(f"Stored dedicated development credential in macOS Keychain service {SERVICE!r}.")
    return 0


def _status() -> int:
    result = _security_capture(
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
    result = _security_capture(
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
    if agent_args and agent_args[0] == "--":
        agent_args = agent_args[1:]
    if not agent_args:
        raise SystemExit("`run` requires arguments for safe_development_agent.py")

    secret = _read_secret()
    secret_bytes = secret.encode("utf-8")
    read_fd, write_fd = os.pipe()
    script = Path(__file__).with_name("safe_development_agent.py")
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env.pop("BOOK_OS_AGENTS_API_KEY", None)
    env["BOOK_OS_AGENTS_API_KEY_FD"] = str(read_fd)

    try:
        os.write(write_fd, secret_bytes)
        os.close(write_fd)
        write_fd = -1
        completed = subprocess.run(
            [sys.executable, str(script), *agent_args],
            env=env,
            pass_fds=(read_fd,),
            check=False,
        )
        return completed.returncode
    finally:
        if write_fd >= 0:
            os.close(write_fd)
        os.close(read_fd)
        env.pop("BOOK_OS_AGENTS_API_KEY_FD", None)
        secret = ""
        secret_bytes = b""


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
