from __future__ import annotations

from typing import cast

# Import installs the Writer gateway wrapper before create_app constructs DraftingService.
from . import drafting_anti_junk as _drafting_anti_junk  # noqa: F401
from .anti_junk import AntiJunkService
from .bookbench import (
    BookBenchService,
    EvaluationRunView,
    EvaluationSnapshotView,
    _CheckResult,
    _FindingDraft,
)
from .bookbench_registry import CheckSpec


def _check_prose_anti_junk(
    service: BookBenchService, snapshot: EvaluationSnapshotView
) -> _CheckResult:
    anti_junk = AntiJunkService(service.projects_dir.parent)
    units = service._manuscript_targets(snapshot)
    findings: list[_FindingDraft] = []
    banned_count = 0
    review_count = 0
    for unit in units:
        for hit in anti_junk.scan(unit.text):
            kind = str(hit["kind"])
            if kind == "BANNED_TEMPLATE":
                banned_count += 1
            else:
                review_count += 1
            findings.append(
                _FindingDraft(
                    target=unit,
                    category=(
                        "PROSE_ANTI_JUNK_TEMPLATE"
                        if kind == "BANNED_TEMPLATE"
                        else "PROSE_ANTI_JUNK_CONTEXT_REVIEW"
                    ),
                    location=f"chars:{hit['start']}-{hit['end']}",
                    evidence={
                        "entry_id": cast(str, hit["entry_id"]),
                        "dictionary_value": cast(str, hit["value"]),
                        "match": cast(str, hit["match"]),
                        "kind": kind,
                        "source": cast(str, hit["source"]),
                        "detector_version": "prose-anti-junk-v0.1",
                    },
                    severity="ATTENTION",
                    confidence=1.0 if kind == "BANNED_TEMPLATE" else 0.75,
                    recommended_action=(
                        "Переформулировать мысль прямо и конкретно; не использовать шаблонную "
                        "нейросетевую/рекламную рамку."
                        if kind == "BANNED_TEMPLATE"
                        else "Проверить контекст: оставить слово только если буквальный смысл необходим."
                    ),
                )
            )
    return _CheckResult(
        findings=findings,
        metrics={
            "banned_template_hit_count": banned_count,
            "context_review_hit_count": review_count,
            "dictionary_entry_count": len(anti_junk.list_entries()),
        },
        output={
            "detector_version": "prose-anti-junk-v0.1",
            "claim": "dictionary/pattern quality signals only; no AI-authorship inference",
        },
    )


def install_anti_junk_bookbench_extension() -> None:
    if getattr(BookBenchService, "_anti_junk_extension_installed", False):
        return

    original_execute = BookBenchService._execute_deterministic
    original_suite = BookBenchService.run_deterministic_suite

    def execute(
        self: BookBenchService, spec: CheckSpec, snapshot: EvaluationSnapshotView
    ) -> _CheckResult:
        if spec.check_id == "deterministic.prose_anti_junk":
            return _check_prose_anti_junk(self, snapshot)
        return original_execute(self, spec, snapshot)

    def suite(
        self: BookBenchService, book_id: str, snapshot_id: str
    ) -> list[EvaluationRunView]:
        runs = original_suite(self, book_id, snapshot_id)
        runs.append(self.run_check(book_id, snapshot_id, "deterministic.prose_anti_junk"))
        return runs

    BookBenchService._execute_deterministic = execute
    BookBenchService.run_deterministic_suite = suite
    BookBenchService._anti_junk_extension_installed = True


install_anti_junk_bookbench_extension()
