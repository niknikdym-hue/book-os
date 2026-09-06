from pathlib import Path
import json

import pytest

from book_os_core.book_context import (
    BookContextGateError,
    BookContextService,
    BookContextUpdateRequest,
    ProfileCreateRequest,
    ProfileRegistry,
    ProfileUpdateRequest,
)
from book_os_core.projects import NewBookRequest, ProjectService


def create_approved_author(registry: ProfileRegistry, name: str = "Елена Дилон"):
    profile = registry.create_profile(
        ProfileCreateRequest(
            kind="AUTHOR",
            content={
                "author_name": name,
                "expertise_constraints": "Не приписывать автору вымышленные регалии.",
                "voice_requirements": "Современная литературно-публицистическая проза.",
                "evidence_discipline": "Материальные утверждения требуют доказательств.",
                "storytelling_expectations": "Сцена существует ради мысли.",
                "rhythm_syntax": "Естественная смена длинных, средних и коротких предложений.",
                "irony_directness_temperature": "Суховатая точная ирония.",
                "prose_prohibitions": ["Психологический туман"],
                "benchmark_excerpts": ["Короткий утверждённый автором benchmark."],
            },
        )
    )
    return registry.approve_profile(profile.profile_id)


def test_profiles_are_versioned_human_approved_and_bound_to_book(tmp_path: Path) -> None:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Контекст книги", primary_subtype="Strategy")
    )
    registry = ProfileRegistry(tmp_path)
    author = create_approved_author(registry)

    series = registry.create_profile(
        ProfileCreateRequest(
            kind="SERIES",
            content={
                "series_name": "Право на себя",
                "author_profile_id": author.profile_id,
                "purpose_positioning": "Самостоятельные книги об отдельных жизненных механизмах.",
                "planned_books": ["Книга 1", "Книга 2"],
                "thematic_territories": ["Каждая книга владеет своей тематической территорией"],
                "shared_invariants": ["Высокая литературная и интеллектуальная плотность"],
                "future_book_reservations": ["Не расходовать темы будущих книг заранее"],
                "cross_book_uniqueness_rules": ["Нулевой смысловой overlap"],
                "exclusion_dimensions": ["тезисы", "сцены", "механизмы", "аналогии"],
                "prewriting_overlap_requirements": ["Карта уникальности до написания"],
                "whole_book_audit_requirements": ["Сквозной cross-book audit"],
            },
        )
    )
    series = registry.approve_profile(series.profile_id)

    style = registry.create_profile(
        ProfileCreateRequest(
            kind="STYLE",
            content={
                "style_name": "Елена Дилон — основной",
                "author_profile_id": author.profile_id,
                "literary_register": "Литературно-публицистический",
                "authorial_presence": "Сильная авторская позиция",
                "directness": "Прямая точная мысль",
                "sentence_paragraph_rhythm": "Варьируемый ритм",
                "scene_density": "Сцены только функциональные",
                "evidence_density": "По необходимости",
                "analytical_depth": "Высокая",
                "irony_humor": "Сухая точная ирония",
                "emotional_temperature": "Сдержанная",
                "practical_instruction_intensity": "Польза встроена в анализ",
                "terminology_level": "Ясный без примитивизации",
                "prohibited_patterns": ["negative-first"],
                "benchmark_excerpts": ["Утверждённый benchmark"],
            },
        )
    )
    style = registry.approve_profile(style.profile_id)

    context = BookContextService(tmp_path).save_context(
        project.book_id,
        BookContextUpdateRequest(
            author_profile_id=author.profile_id,
            series_profile_id=series.profile_id,
            style_profile_id=style.profile_id,
            target_characters=300_000,
            min_characters=280_000,
            max_characters=320_000,
        ),
    )

    assert context.ready_for_planning is True
    assert context.characters_unit == "characters_with_spaces"
    assert context.target_characters == 300_000
    assert context.author_profile is not None
    assert context.author_profile.name == "Елена Дилон"
    assert context.series_profile is not None
    assert context.series_profile.name == "Право на себя"
    assert context.style_profile is not None
    assert context.style_profile.name == "Елена Дилон — основной"


def test_profile_edit_appends_draft_revision_instead_of_silent_overwrite(tmp_path: Path) -> None:
    registry = ProfileRegistry(tmp_path)
    author = create_approved_author(registry)
    updated = registry.update_profile(
        author.profile_id,
        ProfileUpdateRequest(
            content={
                **author.content,
                "voice_requirements": "Обновлённое правило голоса после явной правки автора.",
            }
        ),
    )
    assert updated.status == "DRAFT"
    assert updated.current_revision == 2
    assert updated.content_hash != author.content_hash

    stored = json.loads((tmp_path / "context-profiles.json").read_text(encoding="utf-8"))
    revisions = stored["profiles"][author.profile_id]["revisions"]
    assert len(revisions) == 2
    assert revisions[0]["status"] == "APPROVED"
    assert revisions[1]["status"] == "DRAFT"


def test_series_cannot_be_approved_before_its_author(tmp_path: Path) -> None:
    registry = ProfileRegistry(tmp_path)
    author = registry.create_profile(
        ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Автор"})
    )
    series = registry.create_profile(
        ProfileCreateRequest(
            kind="SERIES",
            content={
                "series_name": "Серия",
                "author_profile_id": author.profile_id,
            },
        )
    )
    with pytest.raises(BookContextGateError, match="approved Author Profile"):
        registry.approve_profile(series.profile_id)


def test_context_rejects_series_or_style_from_another_author(tmp_path: Path) -> None:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Чужой профиль", primary_subtype="Strategy")
    )
    registry = ProfileRegistry(tmp_path)
    author_a = create_approved_author(registry, "Автор A")
    author_b = create_approved_author(registry, "Автор B")
    series_b = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(
                kind="SERIES",
                content={"series_name": "Серия B", "author_profile_id": author_b.profile_id},
            )
        ).profile_id
    )
    style_a = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(
                kind="STYLE",
                content={"style_name": "Стиль A", "author_profile_id": author_a.profile_id},
            )
        ).profile_id
    )

    with pytest.raises(BookContextGateError, match="belongs to another author"):
        BookContextService(tmp_path).save_context(
            project.book_id,
            BookContextUpdateRequest(
                author_profile_id=author_a.profile_id,
                series_profile_id=series_b.profile_id,
                style_profile_id=style_a.profile_id,
                target_characters=300_000,
            ),
        )
