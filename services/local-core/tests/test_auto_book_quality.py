import pytest
from pydantic import ValidationError

from book_os_core.auto_book_exports import MasterChapter, StructuredBookMaster
from book_os_core.auto_book_quality import AutoBookQualityEngine, AutoQualityFinding
from book_os_core.model_gateway import BookBenchJudgeOutput


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


def test_material_claim_extractor_covers_required_external_world_categories() -> None:
    text = " ".join(
        [
            "Исследования показывают, что более ясное обещание результата влияет на выбор клиента.",
            "В 2025 году рынок профессионального обучения изменил структуру спроса.",
            "По словам исследователя Иванова, доверие формируется до сравнения программы курса.",
            "Закон о рекламе требует маркировать определённые рекламные сообщения.",
            "Эксперты сходятся во мнении, что единый показатель без контекста недостаточен.",
            "Платформа сейчас использует обновлённые правила ранжирования материалов.",
            "Наблюдения выявили устойчивый ненумерический паттерн поведения покупателей.",
        ]
    )
    claims = AutoBookQualityEngine.material_claims(text)
    assert len(claims) == 7
    assert any("влияет" in claim for claim in claims)
    assert any("2025 году" in claim for claim in claims)
    assert any("По словам" in claim for claim in claims)
    assert any("Закон" in claim for claim in claims)
    assert any("Эксперты сходятся" in claim for claim in claims)
    assert any("Платформа сейчас" in claim for claim in claims)
    assert any("Наблюдения выявили" in claim for claim in claims)


def test_material_claim_extractor_does_not_treat_authorial_mechanism_as_external_fact() -> None:
    text = (
        "Эта глава предлагает авторскую матрицу выбора. "
        "Сначала читатель формулирует задачу, затем проверяет границы решения."
    )
    assert AutoBookQualityEngine.material_claims(text) == []


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


def test_blocking_critic_result_with_empty_findings_fails_closed() -> None:
    with pytest.raises(ValidationError, match="requires at least one finding"):
        BookBenchJudgeOutput.model_validate(
            {
                "verdict": "BLOCKING",
                "findings": [],
                "confidence": 0.91,
                "rationale": "The exact snapshot is not ready for release.",
            }
        )


@pytest.mark.parametrize(
    "result",
    [
        {
            "verdict": "ATTENTION",
            "confidence": 0.72,
            "rationale": "A material concern remains unresolved.",
        },
        {
            "verdict": "BLOCKING",
            "findings": [
                {
                    "location": "chapter:1",
                    "evidence": "The claim has no current source.",
                }
            ],
            "confidence": 0.88,
            "rationale": "The evidence gate is incomplete.",
        },
    ],
)
def test_malformed_or_incomplete_critic_result_fails_closed(result: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        BookBenchJudgeOutput.model_validate(result)


def test_attention_findings_remain_unresolved_and_preserve_review_evidence() -> None:
    book = master(["Глава объясняет конкретный механизм без внешних утверждений."])
    attention = AutoQualityFinding(
        code="INDEPENDENT_MODEL_CRITIQUE",
        severity="ATTENTION",
        location="chapter:1:paragraph:1",
        evidence="The practical boundary remains ambiguous.",
        required_action="Clarify the boundary and run the exact-snapshot review again.",
    )
    report = AutoBookQualityEngine().review(
        book,
        writer_identity="writer/openai/run-1",
        reviewer_identity="critic/openai/review-1",
        additional_findings=[attention],
        critic_verdict="ATTENTION",
        critic_rationale="One location-specific concern remains unresolved.",
        critic_confidence=0.83,
    )

    assert report.status == "REWORK"
    assert report.finding_counts == {"ATTENTION": 1, "BLOCKING": 0}
    assert report.independent_review.verdict == "ATTENTION"
    assert report.independent_review.rationale == (
        "One location-specific concern remains unresolved."
    )
    assert report.independent_review.confidence == 0.83
    assert report.independent_review.reviewer_identity == "critic/openai/review-1"
    assert (
        AutoBookQualityEngine.may_complete(report, current_master_hash=book.manifest_hash) is False
    )
    assert (
        AutoBookQualityEngine.may_admit_candidate(report, current_master_hash=book.manifest_hash)
        is True
    )


def test_stale_review_cannot_admit_a_changed_candidate() -> None:
    reviewed = master(["Первая версия объясняет границы механизма."])
    report = AutoBookQualityEngine().review(
        reviewed,
        writer_identity="writer/openai/run-1",
        reviewer_identity="critic/openai/review-1",
        critic_verdict="PASS",
        critic_rationale="No release-blocking or attention findings remain.",
        critic_confidence=0.94,
    )
    changed = master(["Изменённая версия иначе объясняет границы механизма."])

    assert report.master_hash != changed.manifest_hash
    assert (
        AutoBookQualityEngine.may_complete(report, current_master_hash=changed.manifest_hash)
        is False
    )


def test_exhausted_correction_budget_with_unresolved_attention_fails_closed() -> None:
    book = master(["Глава сохраняет незакрытое замечание критика."])
    report = AutoBookQualityEngine().review(
        book,
        writer_identity="writer/openai/run-1",
        reviewer_identity="critic/openai/review-2",
        additional_findings=[
            AutoQualityFinding(
                code="INDEPENDENT_MODEL_CRITIQUE",
                severity="ATTENTION",
                location="chapter:1",
                evidence="The requested correction is still absent.",
                required_action="Correct the passage before release.",
            )
        ],
        critic_verdict="ATTENTION",
        critic_rationale="The previous correction did not resolve the finding.",
        critic_confidence=0.89,
        attempts_used=2,
        max_attempts=2,
    )

    assert report.attempts_used == report.max_attempts
    assert report.finding_counts == {"ATTENTION": 1, "BLOCKING": 0}
    assert (
        AutoBookQualityEngine.may_complete(report, current_master_hash=book.manifest_hash) is False
    )
    assert (
        AutoBookQualityEngine.may_admit_candidate(report, current_master_hash=book.manifest_hash)
        is True
    )
