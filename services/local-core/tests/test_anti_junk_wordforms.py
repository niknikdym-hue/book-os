from __future__ import annotations

from pathlib import Path

import pytest

from book_os_core.anti_junk import AntiJunkService


def _banned_matches(service: AntiJunkService, text: str) -> list[str]:
    return [str(hit["match"]) for hit in service.scan(text) if hit["kind"] == "BANNED_TEMPLATE"]


@pytest.mark.parametrize(
    "text",
    [
        "Эта схема стала опорой для всей главы.",
        "Нам нужны опоры для решения.",
        "Теперь вы больше не обязаны действовать по старой схеме.",
        "Эта мысль откликнулась читателю.",
        "Этот пример откликнулся участникам.",
        "Обойдёмся без лишних теорий.",
        "Текст обещает результат без воды.",
        "Действуем без паники.",
    ],
)
def test_owner_requested_junk_wordforms_are_blocked(tmp_path: Path, text: str) -> None:
    service = AntiJunkService(tmp_path)
    assert _banned_matches(service, text)


@pytest.mark.parametrize(
    "text",
    [
        "Для механизма нужен опорный подшипник.",
        "Редактор получил отклик читателя.",
    ],
)
def test_wordform_rules_do_not_expand_to_derivational_relatives(tmp_path: Path, text: str) -> None:
    service = AntiJunkService(tmp_path)
    assert not _banned_matches(service, text)
