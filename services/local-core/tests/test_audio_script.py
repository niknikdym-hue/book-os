from pathlib import Path

import pytest

from book_os_core.audio_script import (
    AudioScriptContent,
    AudioScriptGateError,
    AudioScriptSection,
    AudioScriptService,
    AudioTransformation,
    AudioVisualDecision,
)
from book_os_core.auto_book_exports import AutoBookExporter, MasterChapter, StructuredBookMaster
from book_os_core.auto_book_runtime import (
    AutoBookIntent,
    AutoBookOutputSelection,
    DurableAutoBookRuntime,
)
from book_os_core.projects import NewBookRequest, ProjectService


def setup_book(tmp_path: Path) -> str:
    return (
        ProjectService(tmp_path)
        .create_project(NewBookRequest(working_title="Audio fixture", primary_subtype="Strategy"))
        .book_id
    )


def clean_content(
    *, page_reference: bool = False, blocked_visual: bool = False
) -> AudioScriptContent:
    paragraph = (
        "Смотрите ниже: главный вывод станет понятен после таблицы."
        if page_reference
        else "Сначала слушатель получает контекст, затем механизм и практический вывод."
    )
    return AudioScriptContent(
        title="Проверяемая аудиокнига",
        author="Елена Дым",
        sections=[
            AudioScriptSection(
                source_chapter_id="chapter-1",
                title="Глава первая. Решение",
                paragraphs=[paragraph, "Компания OpenAI проверяет термин CRM и слово замок."],
                visual_decisions=[
                    AudioVisualDecision(
                        object_id="table-1",
                        kind="TABLE",
                        title="Рост конверсии",
                        disposition="BLOCKED" if blocked_visual else "AUDIO_EXPLANATION",
                        placement_after_paragraph=1,
                        explanation=(
                            ""
                            if blocked_visual
                            else "Таблица о росте конверсии показывает: значение 20 увеличилось до 35."
                        ),
                        source_facts=["20", "35", "рост", "конверсия"],
                    )
                ],
            )
        ],
    )


def transformations() -> list[AudioTransformation]:
    return [
        AudioTransformation(
            source_unit_id="chapter-1",
            outcome="REWRITTEN",
            summary="Письменный раздел переработан для последовательного прослушивания.",
        )
    ]


def test_audio_script_is_separate_versioned_human_approved_and_stale_without_destroying_history(
    tmp_path: Path,
) -> None:
    book_id = setup_book(tmp_path)
    service = AudioScriptService(tmp_path)
    source_hash = "a" * 64
    proposed = service.create_proposal(
        book_id,
        source_kind="LITERARY_MASTER",
        source_identity="master-1",
        source_hash=source_hash,
        adaptation_mode="SOURCE_FAITHFUL",
        content=clean_content(),
        transformations=transformations(),
        provenance={"provider": "openai", "model": "gpt-6-astra", "operation": "AUDIO_EDIT"},
    )

    assert proposed.version == 1
    assert proposed.status == "PROPOSED"
    assert proposed.content_hash != source_hash
    with pytest.raises(AudioScriptGateError, match="explicitly disposition"):
        service.approve(book_id, proposed.audio_script_id, human_actor="Owner")

    attention = sorted(
        {
            finding.code
            for check in proposed.quality_checks
            for finding in check.findings
            if finding.severity == "ATTENTION"
        }
    )
    approved = service.approve(
        book_id,
        proposed.audio_script_id,
        human_actor="Owner",
        accepted_attention_codes=attention,
    )
    assert approved.status == "APPROVED"
    assert approved.approval is not None and approved.approval["actor_kind"] == "HUMAN"
    stale = service.get(book_id, approved.audio_script_id, current_source_hash="b" * 64)
    assert stale.stale_against_source is True
    assert stale.status == "APPROVED"
    assert service.get(book_id, approved.audio_script_id).content_hash == approved.content_hash


def test_new_imported_source_marks_prior_audio_script_stale_without_deleting_it(
    tmp_path: Path,
) -> None:
    book_id = setup_book(tmp_path)
    service = AudioScriptService(tmp_path)
    first = service.create_proposal(
        book_id,
        source_kind="IMPORTED_SOURCE",
        source_identity="audio-sources/first.txt",
        source_hash="1" * 64,
        adaptation_mode="SOURCE_FAITHFUL",
        content=clean_content(),
        transformations=transformations(),
        provenance={"workflow": "EXISTING_TEXT_TO_AUDIO", "provider_calls": 0},
    )
    second = service.create_proposal(
        book_id,
        source_kind="IMPORTED_SOURCE",
        source_identity="audio-sources/second.txt",
        source_hash="2" * 64,
        adaptation_mode="SOURCE_FAITHFUL",
        content=clean_content(),
        transformations=transformations(),
        provenance={"workflow": "EXISTING_TEXT_TO_AUDIO", "provider_calls": 0},
    )

    assert service.get(book_id, first.audio_script_id).stale_against_source is True
    assert service.get(book_id, second.audio_script_id).stale_against_source is False
    assert len(service.list_scripts(book_id)) == 2


def test_blocking_page_language_or_visual_dependency_cannot_be_approved(tmp_path: Path) -> None:
    book_id = setup_book(tmp_path)
    service = AudioScriptService(tmp_path)
    for content in (clean_content(page_reference=True), clean_content(blocked_visual=True)):
        proposed = service.create_proposal(
            book_id,
            source_kind="IMPORTED_SOURCE",
            source_identity="source.txt",
            source_hash="c" * 64,
            adaptation_mode="LISTENING_ADAPTATION",
            content=content,
            transformations=transformations(),
            provenance={"provider_calls": 0},
        )
        assert any(item.state == "BLOCKING" for item in proposed.quality_checks)
        with pytest.raises(AudioScriptGateError, match="blocking checks"):
            service.approve(book_id, proposed.audio_script_id, human_actor="Owner")


def test_human_correction_creates_a_new_checked_version_and_preserves_history(
    tmp_path: Path,
) -> None:
    book_id = setup_book(tmp_path)
    service = AudioScriptService(tmp_path)
    blocked = service.create_proposal(
        book_id,
        source_kind="IMPORTED_SOURCE",
        source_identity="source.txt",
        source_hash="e" * 64,
        adaptation_mode="SOURCE_FAITHFUL",
        content=clean_content(page_reference=True),
        transformations=transformations(),
        provenance={"provider_calls": 0},
    )

    tampered = clean_content()
    tampered.sections[0].visual_decisions[0].source_facts = ["35"]
    with pytest.raises(AudioScriptGateError, match="immutable visual metadata"):
        service.revise_by_human(
            book_id,
            blocked.audio_script_id,
            content=tampered,
            human_actor="Owner",
            change_summary="Попытка изменить исходные данные визуального материала.",
        )

    revised = service.revise_by_human(
        book_id,
        blocked.audio_script_id,
        content=clean_content(),
        human_actor="Owner",
        change_summary="Убрана ссылка на страницу; переход переписан для слушателя.",
    )

    assert revised.version == blocked.version + 1
    assert revised.status == "PROPOSED"
    assert revised.provenance["parent_audio_script_id"] == blocked.audio_script_id
    assert revised.provenance["revision_actor_kind"] == "HUMAN"
    assert service.get(book_id, blocked.audio_script_id).status == "SUPERSEDED"
    assert not any(
        item.state == "BLOCKING" and item.check_kind == "PAGE_DEPENDENT_LANGUAGE"
        for item in revised.quality_checks
    )


def test_pronunciation_ledger_covers_names_foreign_acronyms_terms_and_ambiguous_stress(
    tmp_path: Path,
) -> None:
    service = AudioScriptService(tmp_path)
    entries = service.discover_pronunciation(clean_content())
    by_term = {item.term.casefold(): item for item in entries}
    assert by_term["openai"].category == "FOREIGN"
    assert by_term["crm"].category == "ACRONYM"
    assert by_term["замок"].category == "AMBIGUOUS_STRESS"
    assert all(item.status == "NEEDS_REVIEW" for item in entries)
    assert all(item.recommendation is None for item in entries)


def test_audio_docx_cannot_bypass_audio_editorial_approval_and_dictionary_alone_is_cheap(
    tmp_path: Path,
) -> None:
    book_id = setup_book(tmp_path)
    runtime = DurableAutoBookRuntime(tmp_path)
    audio_selection = AutoBookOutputSelection(full_manuscript_docx=False, audio_reading_docx=True)
    run = runtime.create_run(
        book_id,
        AutoBookIntent(
            idea="Аудиоверсия",
            author_name="Автор",
            outputs=audio_selection,
            max_total_cost_usd=5,
            max_cost_usd_per_request=1,
            max_requests=5,
        ),
    )
    master = StructuredBookMaster(
        title="Книга",
        author="Автор",
        chapters=[
            MasterChapter(chapter_id="chapter-1", title="Глава", paragraphs=["Точный текст."])
        ],
    )
    with pytest.raises(AudioScriptGateError, match="cannot be created directly"):
        AutoBookExporter(tmp_path, runtime).export_selected(
            book_id, run.run_id, master, audio_selection
        )

    dictionary_only = AutoBookOutputSelection(
        full_manuscript_docx=False,
        pronunciation_dictionary=True,
    )
    bundle = AutoBookExporter(tmp_path, runtime).export_selected(
        book_id,
        run.run_id,
        master,
        dictionary_only,
    )
    assert [item.output_kind for item in bundle.artifacts] == ["PRONUNCIATION_DICTIONARY"]


def test_audio_native_reuses_approved_listening_master_without_rewrite() -> None:
    service = AudioScriptService(Path("."))
    master = StructuredBookMaster(
        title="Аудиокнига",
        author="Автор",
        chapters=[
            MasterChapter(
                chapter_id="chapter-1",
                title="Глава",
                paragraphs=["Текст сразу написан для последовательного прослушивания."],
            )
        ],
    )
    content, mapping = service.content_from_master(master, adaptation_mode="AUDIO_NATIVE")
    assert content.sections[0].paragraphs == master.chapters[0].paragraphs
    assert mapping[0].outcome == "PRESERVED"


def test_regression_fixture_exposes_every_audio_risk_without_fake_pass(tmp_path: Path) -> None:
    service = AudioScriptService(tmp_path)
    content = AudioScriptContent(
        title="Проверка аудиорисков",
        author="Елена Дым",
        sections=[
            AudioScriptSection(
                source_chapter_id="chapter-risk",
                title="Глава о данных и атрибуции",
                paragraphs=[
                    (
                        "Смотрите выше: 13.09.2026 показатель вырос на 35%, а длинный перечень "
                        "включает исследование, проверку источника, фиксацию оговорки, сравнение "
                        "версий, оценку риска, редактуру, повторную проверку, решение автора и "
                        "подготовку результата для слушателя, который не видит страницу и поэтому "
                        "не может вернуться глазами к началу предложения или к сноске [1]."
                    ),
                    (
                        "По данным OpenAI, термин CRM и слово замок требуют проверки; существенная "
                        "оговорка сохраняется и не превращается в обещание без доказательств."
                    ),
                ],
                visual_decisions=[
                    AudioVisualDecision(
                        object_id="table-risk",
                        kind="TABLE",
                        title="Таблица конверсии",
                        disposition="AUDIO_EXPLANATION",
                        placement_after_paragraph=1,
                        explanation=(
                            "Таблица конверсии показывает рост от 20 до 35 при неизменной выборке; "
                            "это сравнение, а не доказательство причинности."
                        ),
                        source_facts=["20", "35", "не доказательство причинности"],
                    ),
                    AudioVisualDecision(
                        object_id="chart-risk",
                        kind="CHART",
                        title="График динамики",
                        disposition="BLOCKED",
                        placement_after_paragraph=2,
                        source_facts=["январь", "март", "существенная оговорка"],
                    ),
                ],
            )
        ],
    )
    checks = service.evaluate(
        content,
        source_hash="d" * 64,
        mode="SOURCE_FAITHFUL",
        transformations=[
            AudioTransformation(
                source_unit_id="chapter-risk",
                outcome="REWRITTEN",
                summary="Адаптированы список, дата, проценты, сноска и иностранный термин.",
            )
        ],
    )
    by_kind = {item.check_kind: item for item in checks}
    assert by_kind["PAGE_DEPENDENT_LANGUAGE"].state == "BLOCKING"
    assert by_kind["VISUAL_DEPENDENCY_RESOLVED"].state == "BLOCKING"
    assert by_kind["NUMBER_AND_SYMBOL_PRONUNCIATION"].state == "ATTENTION"
    assert by_kind["ACRONYM_AND_TERM_PRONUNCIATION"].state == "ATTENTION"
    assert by_kind["LISTENABILITY"].state == "BLOCKING"
    recording = content.clean_recording_text()
    assert recording.index("Таблица конверсии показывает") > recording.index("Смотрите выше")
    assert recording.index("Таблица конверсии показывает") < recording.index("По данным OpenAI")
