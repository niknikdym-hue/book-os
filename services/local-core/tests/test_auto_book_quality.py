import pytest

from book_os_core.auto_book_exports import MasterChapter, StructuredBookMaster
from book_os_core.auto_book_quality import AutoBookQualityEngine


def master(*paragraphs_by_chapter: list[str]) -> StructuredBookMaster:
    return StructuredBookMaster(
        title="Сквозная проверка",
        author="Тестовый автор",
        chapters=[
            MasterChapter(
                chapter_id=f"chapter-{index}",
                title=f"Глава {index}",
                paragraphs=paragraphs,
            )
            for index, paragraphs in enumerate(paragraphs_by_chapter, start=1)
        ],
    )


def test_unregistered_material_claim_is_detected_even_with_empty_ledger() -> None:
    book = master(
        [
            "По данным исследования, 73 процента клиентов принимают решение за десять минут.",
            "Этот тест не утверждает, что цифра достоверна.",
        ]
    )
    report = AutoBookQualityEngine().review(
        book,
        writer_identity="writer/openai",
        reviewer_identity="critic/independent",
    )
    assert report.status == "REWORK"
    assert {item.code for item in report.findings} == {"UNREGISTERED_MATERIAL_CLAIM"}
    assert not AutoBookQualityEngine.may_complete(report)


def test_evidence_becomes_blocking_after_semantic_revision() -> None:
    claim = "Срок проверки составляет 10 дней."
    book = master([claim])
    current = AutoBookQualityEngine().review(
        book,
        registered_claims={claim: True},
        writer_identity="writer/openai",
        reviewer_identity="critic/independent",
    )
    assert current.status == "PASS"

    changed = master(["Срок проверки составляет 20 дней."])
    stale = AutoBookQualityEngine().review(
        changed,
        registered_claims={claim: False},
        writer_identity="writer/openai",
        reviewer_identity="critic/independent",
    )
    assert stale.status == "REWORK"
    assert any(item.code == "STALE_CLAIM_EVIDENCE" for item in stale.findings)


def test_distant_repeat_and_quantified_contradiction_are_whole_book_findings() -> None:
    repeated = (
        "Длинный механизм решения описывает последовательность наблюдения, выбора критерия, "
        "проверки границ и сохранения результата, чтобы читатель мог повторить действие без "
        "скрытой зависимости от автора книги."
    )
    book = master(
        [repeated, "Срок проверки составляет 10 дней."],
        ["Отдельная глава раскрывает другой механизм."],
        [repeated, "Срок проверки составляет 20 дней."],
    )
    report = AutoBookQualityEngine().review(
        book,
        registered_claims={
            "Срок проверки составляет 10 дней.": True,
            "Срок проверки составляет 20 дней.": True,
        },
        writer_identity="writer/openai",
        reviewer_identity="critic/independent",
    )
    codes = {item.code for item in report.findings}
    assert "DISTANT_PARAGRAPH_REPEAT" in codes
    assert "DISTANT_QUANTIFIED_CONTRADICTION" in codes
    assert report.status == "REWORK"


def test_independent_critic_has_exact_snapshot_and_cannot_equal_writer() -> None:
    book = master(["Глава объясняет конкретный механизм без численных утверждений."])
    with pytest.raises(ValueError, match="must not be the writer"):
        AutoBookQualityEngine().review(
            book,
            writer_identity="same",
            reviewer_identity="same",
        )
    report = AutoBookQualityEngine().review(
        book,
        writer_identity="writer/astra",
        reviewer_identity="critic/astra-independent-context",
    )
    assert report.independent_review.master_hash == book.manifest_hash
    assert report.independent_review.independent is True
    assert len(report.independent_review.summary) >= 40


def test_exhausted_revision_attempts_never_turn_rework_into_pass() -> None:
    book = master(["Срок проверки составляет 10 дней."])
    report = AutoBookQualityEngine().review(
        book,
        writer_identity="writer/astra",
        reviewer_identity="critic/astra-independent-context",
        attempts_used=2,
        max_attempts=2,
    )
    assert report.status == "REWORK"
    assert report.attempts_used == report.max_attempts
    assert AutoBookQualityEngine.may_complete(report) is False
