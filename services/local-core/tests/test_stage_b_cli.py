from __future__ import annotations

import json

from book_os_core.secrets import DictSecretStore
from book_os_core.stage_b_cli import run


def _base_args(tmp_path) -> list[str]:
    return [
        "--data-dir",
        str(tmp_path),
        "--provider",
        "yandex",
        "--model",
        "yandexgpt",
        "--execution-model",
        "gpt://synthetic-folder/yandexgpt/latest",
        "--config-id",
        "latest-discovery",
        "--max-generation",
        "2",
        "--max-embedding",
        "0",
        "--max-total",
        "2",
    ]


def test_cli_preflight_is_zero_live_and_secret_safe(tmp_path, capsys, monkeypatch) -> None:
    sentinel = "CLI-STAGE-B-SECRET-SENTINEL"
    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)
    status = run(
        ["preflight", *_base_args(tmp_path), "--roles", "WRITER,EDITOR"],
        secrets=DictSecretStore({"yandex_ai_studio_api_key": sentinel}),
    )
    assert status == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["state"] == "READY_FOR_OWNER_LIVE_AUTHORIZATION"
    assert payload["credential_state"] == "AVAILABLE"
    assert payload["model"] == "yandexgpt"
    assert payload["execution_model"] == "gpt://synthetic-folder/yandexgpt/latest"
    assert len(payload["plan_hash"]) == 64
    assert sentinel not in output


def test_cli_execute_stays_blocked_without_explicit_live_flag(
    tmp_path, capsys, monkeypatch
) -> None:
    sentinel = "CLI-STAGE-B-BLOCKED-SECRET"
    secrets = DictSecretStore({"yandex_ai_studio_api_key": sentinel})
    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)
    preflight_status = run(
        ["preflight", *_base_args(tmp_path), "--roles", "WRITER"],
        secrets=secrets,
    )
    assert preflight_status == 0
    preflight_output = capsys.readouterr().out
    plan_hash = json.loads(preflight_output)["plan_hash"]

    status = run(
        [
            "writer",
            *_base_args(tmp_path),
            "--authorized-plan-hash",
            plan_hash,
        ],
        secrets=secrets,
    )
    captured = capsys.readouterr()
    assert status == 2
    assert "BOOK_OS_ALLOW_LIVE_PROVIDER=1" in captured.err
    assert sentinel not in captured.err
    assert captured.out == ""


def test_cli_preflight_reports_missing_credential_without_secret_or_network(
    tmp_path, capsys
) -> None:
    status = run(
        ["preflight", *_base_args(tmp_path), "--roles", "WRITER"],
        secrets=DictSecretStore({}),
    )
    assert status == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["credential_state"] == "NOT AVAILABLE"
    assert "CREDENTIAL_MISSING" in payload["blockers"]


def test_cli_yandex_preflight_blocks_without_exact_execution_model(tmp_path, capsys) -> None:
    args = _base_args(tmp_path)
    marker = args.index("--execution-model")
    del args[marker : marker + 2]
    status = run(
        ["preflight", *args, "--roles", "WRITER"],
        secrets=DictSecretStore({"yandex_ai_studio_api_key": "secret"}),
    )
    assert status == 3
    payload = json.loads(capsys.readouterr().out)
    assert "EXECUTION_MODEL_REQUIRED" in payload["blockers"]
