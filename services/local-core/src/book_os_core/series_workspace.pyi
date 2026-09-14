from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from .series_workspace_base import (
    RightsStatus as RightsStatus,
    SeriesBookCreateRequest as SeriesBookCreateRequest,
    SeriesBookLifecycle as SeriesBookLifecycle,
    SeriesBookOrigin as SeriesBookOrigin,
    SeriesBookStatus as SeriesBookStatus,
    SeriesBookView as SeriesBookView,
    SeriesCreateRequest as SeriesCreateRequest,
    SeriesExportSelection as SeriesExportSelection,
    SeriesExportView as SeriesExportView,
    SeriesImportedSourceView as SeriesImportedSourceView,
    SeriesImportRequest as SeriesImportRequest,
    SeriesMapView as SeriesMapView,
    SeriesMutationView as SeriesMutationView,
    SeriesPresetRequest as SeriesPresetRequest,
    SeriesWorkspaceError as SeriesWorkspaceError,
    SeriesWorkspaceGateError as SeriesWorkspaceGateError,
    SeriesWorkspaceService as _BaseSeriesWorkspaceService,
    SeriesWorkspaceView as SeriesWorkspaceView,
)

SeriesScopeRecommendation = Literal["NEW_BOOK", "EXISTING_BOOK_CHAPTER", "REVIEW"]
OverlapClassification = Literal[
    "TERM",
    "SHORT_REMINDER",
    "DEVELOPMENT",
    "NEW_CONTEXT_APPLICATION",
    "UNACCEPTABLE_DUPLICATE",
]

class SeriesBookScopeRequest(BaseModel):
    idea: str
    reader_problem: str = ...
    reader_result: str = ...
    unique_mechanism: str = ...

class SeriesBookScopeAssessment(BaseModel):
    series_profile_id: str
    recommendation: SeriesScopeRecommendation
    confidence: float
    candidate_book_id: str | None = ...
    candidate_book_title: str | None = ...
    evidence: dict[str, Any] = ...

class SeriesTopicOwnershipRequest(BaseModel):
    topic_label: str
    owner_book_id: str
    reason: str

class SeriesTopicOwnershipView(BaseModel):
    ownership_id: str
    series_profile_id: str
    topic_key: str
    topic_label: str
    owner_book_id: str
    owner_book_title: str
    reason: str
    actor: str
    supersedes_ownership_id: str | None = ...
    created_at: str

class SeriesOverlapDispositionRequest(BaseModel):
    classification: OverlapClassification
    reason: str
    topic_label: str | None = ...
    owner_book_id: str | None = ...

class SeriesOverlapDispositionView(BaseModel):
    finding_id: str
    classification: OverlapClassification
    finding_status: Literal["OPEN", "RESOLVED", "ACCEPTED_EXCEPTION"]
    map: SeriesMapView

class SeriesWorkspaceService(_BaseSeriesWorkspaceService):
    def requires_series_review(self, series_profile_id: str) -> bool: ...
    def clear_series_review_requirement(self, series_profile_id: str) -> None: ...
    def assess_book_scope(
        self,
        series_profile_id: str,
        request: SeriesBookScopeRequest,
    ) -> SeriesBookScopeAssessment: ...
    def topic_ownerships(self, series_profile_id: str) -> list[SeriesTopicOwnershipView]: ...
    def assign_topic_ownership(
        self,
        series_profile_id: str,
        request: SeriesTopicOwnershipRequest,
        *,
        actor: str = "HUMAN:OWNER",
    ) -> SeriesTopicOwnershipView: ...
    def dispose_overlap(
        self,
        series_profile_id: str,
        finding_id: str,
        request: SeriesOverlapDispositionRequest,
        *,
        actor: str = "HUMAN:OWNER",
    ) -> SeriesOverlapDispositionView: ...
