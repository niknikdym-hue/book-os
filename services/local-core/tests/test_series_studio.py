import base64
import json
from pathlib import Path

from book_os_core.book_context import ProfileCreateRequest, ProfileRegistry
from book_os_core.model_gateway import ModelAdapterResult, ModelGateway
from book_os_core.series_reference import SeriesReferenceService, SeriesReferenceUploadRequest
from book_os_core.series_studio import SeriesCreateWithAIRequest, SeriesStudioService


class SeriesProposalAdapter:
    provider_name = "openai"

    def generate(self, request, prompt):
        assert request.role == "PLANNER"
        assert prompt.prompt_id == "series_profile_proposal_v1"
        proposal = {
            "series_name": "Секреты продвижения услуг",
            "purpose_positioning": "Самостоятельные книги о разных задачах продвижения услуг.",
            "planned_books": ["Как продавать услуги", "Как выстроить поток рекомендаций"],
            "thematic_territories": [
                "Книга 1 — система продажи услуги",
                "Книга 2 — система рекомендаций без повторения продажной механики",
            ],
            "shared_invariants": ["Высокая практическая и аналитическая плотность"],
            "future_book_reservations": ["Реферальная система принадлежит книге 2"],
            "cross_book_uniqueness_rules": [],
            "exclusion_dimensions": [],
            "prewriting_overlap_requirements": [],
            "whole_book_audit_requirements": [],
        }
        return ModelAdapterResult(
            provider_run_id="series-proposal-run",
            output={"text": json.dumps(proposal, ensure_ascii=False), "notes": []},
            usage={"input_tokens": 300, "output_tokens": 450},
        )


def approved_author(registry: ProfileRegistry):
    author = registry.create_profile(
        ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Елена Дымова"})
    )
    return registry.approve_profile(author.profile_id)


def test_ai_series_proposal_is_hardened_against_cross_book_cloning(tmp_path: Path) -> None:
    registry = ProfileRegistry(tmp_path)
    author = approved_author(registry)
    service = SeriesStudioService(
        tmp_path,
        ModelGateway({"openai": SeriesProposalAdapter()}),
    )

    result = service.create_with_ai(
        SeriesCreateWithAIRequest(
            author_profile_id=author.profile_id,
            brief="Новая серия о продвижении услуг. Каждая книга решает отдельную задачу бизнеса.",
            model_choice="SOL",
            max_cost_usd=1.0,
            owner_authorizes_paid_call=True,
        )
    )

    assert result.model == "gpt-5.6-sol"
    assert result.reasoning_effort is None
    assert result.profile.status == "DRAFT"
    content = result.profile.content
    assert content["series_name"] == "Секреты продвижения услуг"
    assert (
        "Запрещён смысловой overlap с другими книгами серии."
        in content["cross_book_uniqueness_rules"]
    )
    assert "метафоры и аналогии" in content["exclusion_dimensions"]
    assert any(
        "cross-book overlap map" in value for value in content["prewriting_overlap_requirements"]
    )
    assert any("SeriesBench" in value for value in content["whole_book_audit_requirements"])


def test_existing_series_reference_is_style_evidence_not_content_source(tmp_path: Path) -> None:
    registry = ProfileRegistry(tmp_path)
    author = approved_author(registry)
    series = registry.create_profile(
        ProfileCreateRequest(
            kind="SERIES",
            content={
                "series_name": "Секреты продвижения услуг",
                "author_profile_id": author.profile_id,
                "purpose_positioning": "Самостоятельные книги о разных задачах продвижения услуг.",
                "planned_books": ["Как продавать услуги"],
                "cross_book_uniqueness_rules": ["Нулевой смысловой overlap"],
                "exclusion_dimensions": ["тезисы", "механизмы", "аналогии"],
            },
        )
    )
    series = registry.approve_profile(series.profile_id)

    paragraphs = [
        (
            "Это эталонный абзац о манере подачи материала. Он показывает ритм, глубину разбора, "
            "плотность объяснения и переход от наблюдения к механизму. Содержание этого текста "
            "никогда не должно становиться материалом другой книги серии."
        )
        for _ in range(40)
    ]
    source = "\n\n".join(paragraphs).encode("utf-8")
    service = SeriesReferenceService(tmp_path)
    reference = service.upload(
        series.profile_id,
        SeriesReferenceUploadRequest(
            filename="Как-продавать-услуги.txt",
            content_base64=base64.b64encode(source).decode("ascii"),
            title="Как продавать услуги — обновлённая редакция",
            owner_approves_derived_style=True,
        ),
    )

    assert reference.role == "DELIVERY_STYLE_REFERENCE"
    assert reference.characters >= 4000
    assert reference.representative_excerpts
    assert "not a content source" not in reference.usage_policy.lower()
    assert "Never reuse" in reference.usage_policy
    current = service.current(series.profile_id)
    assert current is not None
    assert current.reference_id == reference.reference_id
    assert current.text_sha256 == reference.text_sha256

    style = registry.get_profile(reference.style_profile_id)
    assert style.kind == "STYLE"
    assert style.status == "APPROVED"
    assert style.content["author_profile_id"] == author.profile_id
    assert style.content["benchmark_excerpts"]
    prohibited = style.content["prohibited_patterns"]
    assert (
        "Не повторять сцены, примеры, кейсы, метафоры и аналогии других книг серии." in prohibited
    )
    assert (
        "Не копировать структуру глав, последовательность раскрытия мысли и distinctive wording эталона."
        in prohibited
    )
