from book_os_core.auto_book_gates import AutoBookEvidenceGates
from book_os_core.model_gateway import BookConceptProposalOutput


def _concept() -> BookConceptProposalOutput:
    return BookConceptProposalOutput(
        essence="Лиловый чайник объясняет квадратную тишину облаков",
        reader_job="Собрать лиловый чайник для квадратной тишины",
        reader_problem="Квадратная тишина мешает облачным чайникам двигаться",
        reader_transformation="Облачный чайник применяет лиловую квадратную тишину иначе",
        central_idea="Лиловый чайник связывает квадратную тишину с облаками",
        central_promise="Читатель получит квадратную карту лиловых облачных чайников",
        differentiation="Метод отличает облака через лиловый чайник и квадратную тишину",
        why_now="Сейчас лиловые облака особенно квадратны для чайника",
        scope_in=["Лиловые чайники и квадратные облака"],
        scope_out=["Обычная кухня и реальная метеорология"],
        series_place="Отдельная книга про квадратную тишину лиловых чайников",
        overlap_risks=[],
    )


def test_structural_preflight_never_claims_semantic_quality() -> None:
    concept = _concept()
    contract = {
        "reader": "Читатель лиловых квадратных облачных чайников",
        "reader_problem": "Квадратная тишина мешает облачным чайникам двигаться",
        "central_promise": "Получить карту квадратных лиловых облачных чайников",
        "central_thesis": "Лиловый чайник объясняет квадратную тишину через облачные связи",
        "unique_angle": "Квадратная облачная тишина рассматривается через лиловый чайник",
        "reader_trajectory": "От тишины облака к квадратной карте лилового чайника",
        "explicit_exclusions": ["Реальная метеорология"],
        "readiness_criteria": ["Карта собрана"],
    }
    result = AutoBookEvidenceGates.definition(contract, concept)
    # The deliberately nonsensical copy can satisfy several token-count checks.  The contract is
    # nevertheless only STRUCTURAL_PREFLIGHT evidence and cannot be called semantic quality.
    assert any(item.status == "PASS" for item in result.checks)
    assert all(item.evaluation_scope == "STRUCTURAL_PREFLIGHT" for item in result.checks)
    assert all(item.semantic_quality_claimed is False for item in result.checks)


def test_gate_schema_labels_even_top_tier_name_as_structural_only() -> None:
    result = AutoBookEvidenceGates.definition(
        {
            "reader": "Практикующий консультант с собственной услугой",
            "reader_problem": "Не понимает почему заявки не превращаются в продажи",
            "central_promise": "Найти и исправить узкие места системы продаж услуги",
            "central_thesis": "Продажа услуги зависит от последовательности проверяемых решений клиента",
            "unique_angle": "Диагностика потерь связывает каждое решение с измеримым действием",
            "reader_trajectory": "От хаотичных действий к измеримой системе решений и проверок",
            "explicit_exclusions": ["Создание самой услуги"],
            "readiness_criteria": ["Каждый этап имеет проверяемый результат"],
        },
        BookConceptProposalOutput(
            essence="Система продаж услуги",
            reader_job="Продать профессиональную услугу предсказуемо",
            reader_problem="Заявки не превращаются в оплаченные сделки",
            reader_transformation="Читатель управляет измеримой системой продаж своей услуги",
            central_idea="Каждая продажа состоит из последовательности решений клиента",
            central_promise="Диагностировать потери и исправить конкретные этапы продаж",
            differentiation="Фокус на экономике и решениях вместо набора рекламных приемов",
            why_now="Стоимость привлечения растет и ошибки системы становятся дороже",
            scope_in=["Диагностика воронки"],
            scope_out=["Разработка продукта"],
            series_place="Базовая книга о системе продаж услуг",
            overlap_risks=[],
        ),
    )
    check = next(item for item in result.checks if item.gate == "top_tier_global")
    assert check.evaluation_scope == "STRUCTURAL_PREFLIGHT"
    assert check.semantic_quality_claimed is False
