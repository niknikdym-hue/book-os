from pathlib import Path

from book_os_core.book_context import ProfileCreateRequest, ProfileRegistry
from book_os_core.series_workspace import (
    SeriesBookCreateRequest,
    SeriesCreateRequest,
    SeriesWorkspaceService,
)


def test_series_map_hash_ignores_workflow_state_but_tracks_semantic_boundaries(
    tmp_path: Path,
) -> None:
    registry = ProfileRegistry(tmp_path)
    author = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Тестовый автор"})
        ).profile_id
    )
    service = SeriesWorkspaceService(tmp_path)
    series = service.create_series(
        SeriesCreateRequest(
            series_name="Проверка карты",
            author_profile_id=author.profile_id,
            audience="Практики",
            promise="Каждая книга решает отдельную задачу",
            territory="Проверяемая территория",
        )
    )
    registry.approve_profile(series.profile_id)
    service.add_book(
        series.profile_id,
        SeriesBookCreateRequest(
            title="Первая книга",
            ordinal=1,
            unique_idea="Отдельный механизм диагностики спроса",
            reader_problem="Неясно, где возникает ограничение",
            reader_result="Читатель находит конкретное ограничение",
            unique_mechanism="Карта причин ограничения",
        ),
    )

    books = service.books(series.profile_id)
    baseline = service._map_hash(series.profile_id, books)
    workflow_only = [
        book.model_copy(
            update={
                "status": "EDITING",
                "lifecycle": "EDITING",
                "updated_at": "2099-01-01T00:00:00Z",
            }
        )
        for book in books
    ]
    assert service._map_hash(series.profile_id, workflow_only) == baseline

    changed_boundary = [
        books[0].model_copy(update={"unique_idea": "Совершенно другой центральный механизм"})
    ]
    assert service._map_hash(series.profile_id, changed_boundary) != baseline
