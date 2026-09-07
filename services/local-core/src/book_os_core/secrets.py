from __future__ import annotations

from dataclasses import dataclass, field
import subprocess
from typing import Protocol


class SecretStore(Protocol):
    def get_secret(self, name: str) -> str: ...


class SecretNotFound(RuntimeError):
    pass


class SecretWriteError(RuntimeError):
    pass


@dataclass
class DictSecretStore:
    """In-memory test/development secret store. Never serialize its values."""

    values: dict[str, str] = field(default_factory=dict, repr=False)

    def get_secret(self, name: str) -> str:
        try:
            return self.values[name]
        except KeyError as exc:
            raise SecretNotFound(name) from exc


@dataclass(frozen=True)
class MacOSKeychainSecretStore:
    service_prefix: str = "book-os"
    account: str = "book-os"

    def get_secret(self, name: str) -> str:
        service = f"{self.service_prefix}.{name}"
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-a",
                self.account,
                "-s",
                service,
                "-w",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise SecretNotFound(name)
        secret = result.stdout.rstrip("\n")
        if not secret:
            raise SecretNotFound(name)
        return secret

    def set_secret(self, name: str, value: str) -> None:
        secret = value.strip()
        if not secret:
            raise SecretWriteError("secret must not be blank")
        service = f"{self.service_prefix}.{name}"
        result = subprocess.run(
            [
                "/usr/bin/security",
                "add-generic-password",
                "-U",
                "-a",
                self.account,
                "-s",
                service,
                "-w",
                secret,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise SecretWriteError("macOS Keychain refused credential update")
