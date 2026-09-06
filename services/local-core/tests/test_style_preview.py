from pathlib import Path

from sqlalchemy import text

from book_os_core.book_context import ProfileCreateRequest, ProfileRegistry
from book_os_core.db import create_database
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.style_preview import StylePreviewRequest, StylePreviewService


def approved_author(registry: ProfileRegistry):
    draft = registry.create_profile(
        ProfileCreateRequest(
            kind="AUTHOR",
            content={
                "author_name": "Автор",
                "voice_requirements": "Точная современная русская проза",
                "prose_prohibitions": ["negative-first"],
            },
        )
    )
    return registry.approve_profile(draft.profile_id)


def style(registry: ProfileRegistry, author_id: str, name: str, register: str):
    return registry.create_profile(
        ProfileCreateRequest(
            kind="STYLE",
            content={
                "style_name": name,
                "author_profile_id": author_id,
                "literary_register": register,
                "prohibited_patterns": ["шаблонная мотивационная формула"],
            },
        )
    )


def test_same_brief_is_rendered_for_two_profiles_without_manuscript_mutation(
    tmp_path: Path,
) -> None:
    project_service = ProjectService(tmp_path)
    project = project_service.create_project(
        NewBookRequest(working_title="Стилевой тест", primary_subtype="Strategy")
    )
    registry = ProfileRegistry(tmp_path)
    author = approved_author(registry)
    style_a = style(registry, author.profile_id, "Аналитический", "Плотный аналитический")
    style_b = style(registry, author.profile_id, "Сценический", "Сценический литературный")

    fake = DeterministicFakeAdapter()
    service = StylePreviewService(
        tmp_path,
        ModelGateway({"openai": fake, "yandex": DeterministicFakeAdapter()}),
    )
    brief = (
        "Показать, как руководитель незаметно становится узким местом компании, когда все решения "
        "возвращаются к нему на согласование."
    )
    result = service.generate(
        project.book_id,
        StylePreviewRequest(
            author_profile_id=author.profile_id,
            style_profile_ids=[style_a.profile_id, style_b.profile_id],
            content_brief=brief,
            provider="openai",
            selection_mode="AUTO",
            max_cost_usd_per_request=0.20,
        ),
    )

    assert len(result.previews) == 2
    assert result.previews[0].style_name == "Аналитический"
    assert result.previews[1].style_name == "Сценический"
    assert result.brief_hash
    assert result.total_cap_usd == 0.40
    assert all(item.provider == "openai" for item in result.previews)
    assert all(item.model == "gpt-5.6-terra" for item in result.previews)
    assert all(item.text.startswith("Draft for:") for item in result.previews)

    unchanged = project_service.get_project(project.book_id)
    assert unchanged.book_contract is None
    assert unchanged.architecture is None
    assert unchanged.chapters == []

    engine = create_database(project_service.projects_dir / project.book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT brief_hash,style_profile_hash,prompt_id,status FROM style_preview_runs "
                    "WHERE batch_id=:batch_id ORDER BY created_at"
                ),
                {"batch_id": result.batch_id},
            ).mappings().all()
    finally:
        engine.dispose()

    assert len(rows) == 2
    assert rows[0]["brief_hash"] == rows[1]["brief_hash"] == result.brief_hash
    assert rows[0]["style_profile_hash"] != rows[1]["style_profile_hash"]
    assert all(row["prompt_id"] == "style_preview_v1" for row in rows)
    assert all(row["status"] == "SUCCEEDED" for row in rows)


def test_manual_whole_book_selection_from_preview_persists_explicit_pin(tmp_path: Path) -> None:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Pin from preview", primary_subtype="Strategy")
    )
    registry = ProfileRegistry(tmp_path)
    author = approved_author(registry)
    style_a = style(registry, author.profile_id, "Первый", "Первый регистр")
    style_b = style(registry, author.profile_id, "Второй", "Второй регистр")

    service = StylePreviewService(
        tmp_path,
        ModelGateway({"openai": DeterministicFakeAdapter(), "yandex": DeterministicFakeAdapter()}),
    )
    result = service.generate(
        project.book_id,
        StylePreviewRequest(
            author_profile_id=author.profile_id,
            style_profile_ids=[style_a.profile_id, style_b.profile_id],
            content_brief="Один и тот же содержательный brief для явного выбора модели на всю книгу.",
            provider="openai",
            selection_mode="MANUAL",
            selection_scope="BOOK",
            model="gpt-6-astra",
            max_cost_usd_per_request=0.50,
        ),
    )

    assert all(item.model == "gpt-6-astra" for item in result.previews)
    assert all(item.selection_scope == "BOOK" for item in result.previews)
    pin = service.routing.get_book_pin(project.book_id)
    assert pin is not None
    assert pin.provider == "openai"
    assert pin.model == "gpt-6-astra"
