from __future__ import annotations

import base64
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from book_os_core.book_context import ProfileCreateRequest, ProfileRegistry
from book_os_core.context_api import build_context_router
from book_os_core.db import create_database
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import BookArchitecturePayload, BookContractPayload, ProjectService
from book_os_core.series_studio_api import build_series_studio_router
from book_os_core.series_workspace import (
    SeriesBookCreateRequest,
    SeriesBookScopeRequest,
    SeriesCreateRequest,
    SeriesImportRequest,
    SeriesOverlapDispositionRequest,
    SeriesTopicOwnershipRequest,
    SeriesWorkspaceService,
)


def _author(tmp_path: Path) -> str:
    registry = ProfileRegistry(tmp_path)
    author = registry.create_profile(
        ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Тестовый автор"})
    )
    return registry.approve_profile(author.profile_id).profile_id


def _series(tmp_path: Path) -> tuple[SeriesWorkspaceService, str]:
    service = SeriesWorkspaceService(tmp_path)
    profile = service.create_series(
        SeriesCreateRequest(
            series_name="Управляемая серия",
            author_profile_id=_author(tmp_path),
            audience="Практики",
            promise="Каждая книга решает самостоятельную задачу",
            territory="Продажи профессиональных услуг",
        )
    )
    return service, profile.profile_id


def _book(title: str, ordinal: int, idea: str, *, source_kind: str = "PLANNED"):
    return SeriesBookCreateRequest(
        title=title,
        ordinal=ordinal,
        unique_idea=idea,
        reader_problem=f"Проблема: {idea}",
        reader_result=f"Результат: {idea}",
        unique_mechanism=f"Механизм: {idea}",
        source_kind=source_kind,
        origin_kind="IMPORTED" if source_kind == "IMPORTED" else "NEW",
    )


def test_new_book_scope_gate_flags_idea_that_belongs_inside_existing_book(tmp_path: Path) -> None:
    service, series_id = _series(tmp_path)
    existing = service.add_book(
        series_id,
        _book(
            "Доверие до покупки",
            1,
            "Снизить риск выбора клиента через доказательства результата и доверие до оплаты",
        ),
    )

    assessment = service.assess_book_scope(
        series_id,
        SeriesBookScopeRequest(
            idea="Уменьшить неопределённость покупателя доказательствами эффекта до сделки",
            reader_problem="Клиент не уверен в результате до покупки",
            reader_result="Клиент принимает обоснованное решение",
            unique_mechanism="Подтверждения результата снижают риск выбора",
        ),
    )

    assert assessment.recommendation == "EXISTING_BOOK_CHAPTER"
    assert assessment.candidate_book_id == existing.book_id
    assert assessment.confidence >= 0.74
    assert assessment.evidence["provider_calls"] == 0


def test_topic_ownership_is_append_only_and_visible_in_generation_context(tmp_path: Path) -> None:
    service, series_id = _series(tmp_path)
    first = service.add_book(series_id, _book("Книга про спрос", 1, "Диагностика реального спроса"))
    second = service.add_book(
        series_id,
        _book("Книга про предложение", 2, "Конструкция предложения и результата"),
    )

    ownership = service.assign_topic_ownership(
        series_id,
        SeriesTopicOwnershipRequest(
            topic_label="Доказательства результата до покупки",
            owner_book_id=second.book_id,
            reason="Эта книга развивает тему; первая может только кратко напомнить термин.",
        ),
    )
    listed = service.topic_ownerships(series_id)
    assert [item.ownership_id for item in listed] == [ownership.ownership_id]
    assert listed[0].owner_book_id == second.book_id

    context = service.generation_context(first.book_id)
    assert context is not None
    assert context["topic_ownership"][0]["owner_book_id"] == second.book_id

    engine = create_database(tmp_path / "projects" / first.book_id / "project.sqlite")
    try:
        with pytest.raises(IntegrityError, match="append-only"):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE series_topic_ownership SET reason='forbidden' "
                        "WHERE ownership_id=:id"
                    ),
                    {"id": ownership.ownership_id},
                )
    finally:
        engine.dispose()


def test_overlap_disposition_records_exception_and_unblocks_resolved_map(tmp_path: Path) -> None:
    service, series_id = _series(tmp_path)
    first = service.add_book(
        series_id,
        _book(
            "Первая книга",
            1,
            "Клиент выбирает услугу через доверие доказательства результата цену и риск",
        ),
    )
    service.add_book(
        series_id,
        _book(
            "Вторая книга",
            2,
            "Покупатель выбирает услугу через доверие подтверждения результата стоимость и риск",
        ),
    )
    result = service.analyze(series_id)
    assert result.status == "BLOCKING"
    open_overlap = [
        item
        for item in result.findings
        if item.get("status", "OPEN") == "OPEN" and item["dimension"] != "SOURCE_QUALITY"
    ]
    assert open_overlap

    latest = result
    for index, finding in enumerate(open_overlap):
        classification = "DEVELOPMENT" if index == 0 else "SHORT_REMINDER"
        disposition = service.dispose_overlap(
            series_id,
            finding["finding_id"],
            SeriesOverlapDispositionRequest(
                classification=classification,
                reason="Автор явно распределил допустимое пересечение и запретил дублирование развития.",
                topic_label="Доверие и доказательства" if index == 0 else None,
                owner_book_id=first.book_id if index == 0 else None,
            ),
        )
        latest = disposition.map
        assert disposition.finding_status == "ACCEPTED_EXCEPTION"

    assert latest.status != "BLOCKING"
    assert service.topic_ownerships(series_id)[0].owner_book_id == first.book_id

    engine = create_database(tmp_path / "projects" / first.book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            decisions = connection.execute(
                text(
                    "SELECT COUNT(*) FROM series_author_decisions "
                    "WHERE series_profile_id=:series AND decision_kind='EXCEPTION'"
                ),
                {"series": series_id},
            ).scalar_one()
    finally:
        engine.dispose()
    assert decisions == len(open_overlap)


def test_duplicate_scan_reads_relevant_material_beyond_first_20k_characters(tmp_path: Path) -> None:
    service, series_id = _series(tmp_path)
    first = service.add_book(
        series_id,
        _book("Длинная первая", 1, "Первая отдельная территория", source_kind="IMPORTED"),
    )
    second = service.add_book(
        series_id,
        _book("Длинная вторая", 2, "Вторая отдельная территория", source_kind="IMPORTED"),
    )
    prefix_one = ("Уникальный вводный материал первой книги без общего кейса.\n" * 500)
    prefix_two = ("Совершенно иной вводный материал второй книги без общего кейса.\n" * 500)
    duplicate = (
        "Например клиент сравнивает доказательства результата цену и риск перед решением о покупке."
    )
    assert len(prefix_one) > 20_000 and len(prefix_two) > 20_000
    for entry, filename, content in (
        (first, "first.txt", prefix_one + duplicate),
        (second, "second.txt", prefix_two + duplicate),
    ):
        service.import_source(
            series_id,
            entry.book_id,
            SeriesImportRequest(
                filename=filename,
                content_base64=base64.b64encode(content.encode()).decode(),
                rights_status="AUTHOR_MANUSCRIPT",
            ),
        )

    result = service.analyze(series_id)
    assert result.status == "BLOCKING"
    examples = [item for item in result.findings if item["dimension"] == "EXAMPLE"]
    assert examples, "the repeated case after character 20,000 must be inspected"


def test_series_lifecycle_tracks_actual_book_authority_progress(tmp_path: Path) -> None:
    service, series_id = _series(tmp_path)
    entry = service.add_book(series_id, _book("Живая книга", 1, "Построить отдельный механизм"))
    assert service.books(series_id)[0].lifecycle == "PLANNED"

    projects = ProjectService(tmp_path)
    projects.save_book_contract(
        entry.book_id,
        BookContractPayload(
            reader="Практик",
            reader_problem="Неясна система решений",
            central_promise="Получить проверяемую систему",
            central_thesis="Явные критерии делают работу управляемой",
            unique_angle="Разобрать наблюдаемые решения",
            reader_trajectory="От симптома к самостоятельному решению",
            explicit_exclusions=["Не каталог советов"],
            evidence_policy="Материальные утверждения требуют evidence",
            voice_genre_constraints="Практический нон-фикшн",
            readiness_criteria=["Читатель применяет критерий"],
        ),
    )
    projects.approve_book_contract(entry.book_id)
    definition = service.books(series_id)[0]
    assert definition.status == "DEFINITION"
    assert definition.lifecycle == "DEFINITION"

    projects.save_architecture(
        entry.book_id,
        BookArchitecturePayload.model_validate(
            {
                "parts": [
                    {
                        "title": "Часть",
                        "purpose": "Собрать решение",
                        "chapters": [
                            {
                                "title": "Глава",
                                "purpose": "Диагностировать причину",
                                "new_contribution": "Проверяемый критерий",
                            }
                        ],
                    }
                ],
                "intellectual_progression": "От причины к решению",
                "concept_allocation": "Одна глава — одна функция",
                "promise_thesis_coverage": "Обещание закрыто архитектурой",
                "major_transitions": "Диагноз открывает действие",
            }
        ),
    )
    projects.approve_architecture(entry.book_id)
    architecture = service.books(series_id)[0]
    assert architecture.status == "ARCHITECTURE"
    assert architecture.lifecycle == "ARCHITECTURE"


def test_external_series_profile_stays_draft_until_import_analysis(tmp_path: Path) -> None:
    token = "test-token"
    gateway = ModelGateway({"openai": DeterministicFakeAdapter()})
    app = FastAPI()

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if authorization != f"Bearer {token}":
            raise HTTPException(status_code=401, detail="unauthorized")

    app.include_router(build_context_router(tmp_path, require_token, gateway))
    app.include_router(build_series_studio_router(tmp_path, require_token, gateway))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}
    author_id = _author(tmp_path)

    created = client.post(
        "/api/series/workspaces",
        headers=headers,
        json={
            "series_name": "Внешняя серия",
            "author_profile_id": author_id,
            "audience": "Практики",
            "promise": "Отдельные результаты",
            "territory": "Профессиональная работа",
        },
    )
    assert created.status_code == 200
    series_id = created.json()["profile_id"]
    premature = client.post(f"/api/context/profiles/{series_id}/approve", headers=headers)
    assert premature.status_code == 200
    assert premature.json()["status"] == "DRAFT"

    added = client.post(
        f"/api/series/{series_id}/books",
        headers=headers,
        json={
            "title": "Импортированная книга",
            "ordinal": 1,
            "unique_idea": "Самостоятельная задача существующей книги",
            "reader_problem": "Проблема книги",
            "reader_result": "Результат книги",
            "unique_mechanism": "Механизм книги",
            "source_kind": "IMPORTED",
            "origin_kind": "IMPORTED",
        },
    )
    assert added.status_code == 200
    book_id = added.json()["book_id"]
    imported = client.post(
        f"/api/series/{series_id}/books/{book_id}/imports",
        headers=headers,
        json={
            "filename": "book.txt",
            "content_base64": base64.b64encode("Полный текст авторской книги".encode()).decode(),
            "rights_status": "AUTHOR_MANUSCRIPT",
        },
    )
    assert imported.status_code == 200

    still_early = client.post(f"/api/context/profiles/{series_id}/approve", headers=headers)
    assert still_early.status_code == 409
    analyzed = client.post(f"/api/series/{series_id}/analyze", headers=headers)
    assert analyzed.status_code == 200
    assert analyzed.json()["status"] == "PASS"
    approved = client.post(f"/api/context/profiles/{series_id}/approve", headers=headers)
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
