from __future__ import annotations

import json
from pathlib import Path

from book_os_core.db import create_database
from book_os_core.provider_lane import ProviderLaneService
from book_os_core.stage_b_owner import run


def _lane(tmp_path: Path) -> ProviderLaneService:
    return ProviderLaneService(create_database(tmp_path / "provider-lane.sqlite"))


def _promotion_args(tmp_path: Path, *, provider: str, model: str, config_id: str) -> list[str]:
    return [
        "promote",
        "--data-dir",
        str(tmp_path),
        "--provider",
        provider,
        "--model",
        model,
        "--config-id",
        config_id,
        "--role",
        "WRITER",
        "--dataset-hash",
        "d" * 64,
        "--scorecard-ref",
        f"m8-stage-b:{provider}:writer",
        "--reason",
        "Owner-reviewed synthetic Stage B evidence passed required gates",
        "--actor",
        "CENTRAL_BRAIN_TEST",
        "--quality-floor-passed",
        "--confirm-owner-promotion",
    ]


def test_owner_promotion_is_blocked_without_explicit_environment_gate(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("BOOK_OS_ALLOW_PROVIDER_PROMOTION", raising=False)
    status = run(
        _promotion_args(
            tmp_path,
            provider="yandex",
            model="yandexgpt",
            config_id="latest-discovery",
        )
    )
    assert status == 2
    assert "BOOK_OS_ALLOW_PROVIDER_PROMOTION=1" in capsys.readouterr().err
    assert _lane(tmp_path).promotion_evidence() == []


def test_owner_promotion_records_only_after_explicit_gate_and_confirmation(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.setenv("BOOK_OS_ALLOW_PROVIDER_PROMOTION", "1")
    status = run(
        _promotion_args(
            tmp_path,
            provider="yandex",
            model="yandexgpt",
            config_id="latest-discovery",
        )
    )
    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PROMOTED"
    evidence = _lane(tmp_path).promotion_evidence()
    assert len(evidence) == 1
    assert evidence[0]["decision"] == "PROMOTED"
    assert evidence[0]["role"] == "WRITER"


def test_owner_fallback_simulation_uses_promoted_live_healthy_alternative_without_network(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.setenv("BOOK_OS_ALLOW_PROVIDER_PROMOTION", "1")
    assert (
        run(
            _promotion_args(
                tmp_path,
                provider="gigachat",
                model="GigaChat-2-Pro",
                config_id="b2b",
            )
        )
        == 0
    )
    capsys.readouterr()
    assert (
        run(
            _promotion_args(
                tmp_path,
                provider="yandex",
                model="yandexgpt",
                config_id="latest-discovery",
            )
        )
        == 0
    )
    capsys.readouterr()

    lane = _lane(tmp_path)
    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    for provider, model, config_id in (
        ("gigachat", "GigaChat-2-Pro", "b2b"),
        ("yandex", "yandexgpt", "latest-discovery"),
    ):
        lane.record_probe(
            provider=provider,
            model=model,
            config_id=config_id,
            region="RU",
            capability="generation",
            outcome="SUCCESS",
            probe_type="LIVE",
        )
    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)

    status = run(
        [
            "fallback",
            "--data-dir",
            str(tmp_path),
            "--role",
            "WRITER",
            "--unavailable-provider",
            "gigachat",
            "--unavailable-model",
            "GigaChat-2-Pro",
            "--unavailable-config-id",
            "b2b",
        ]
    )
    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["available"] is True
    assert payload["provider"] == "yandex"
    assert payload["model"] == "yandexgpt"
    assert _lane(tmp_path).route("WRITER").capability.provider == "gigachat"
