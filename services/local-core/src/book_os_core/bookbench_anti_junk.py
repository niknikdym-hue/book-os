from __future__ import annotations

from .anti_junk import AntiJunkService
from .bookbench import (
    BookBenchService,
    EvaluationSnapshotView,
    EvaluationRunView,
    _CheckResult,
    _FindingDraft,
)
from .bookbench_registry import CheckSpec


class AntiJunkBookBenchService(BookBenchService):
    def __init__(self, data_dir, embedding_gateway=None, model_gateway=None):
        super().__init__(data_dir, embedding_gateway, model_gateway)
        self.anti_junk = AntiJunkService(data_dir)

    def _check_prose_anti_junk(self, snapshot: EvaluationSnapshotView) -> _CheckResult:
        units = self._manuscript_targets(snapshot)
        findings: list[_FindingDraft] = []
        banned_count = 0
        review_count = 0
        for unit in units:
            for hit in self.anti_junk.scan(unit.text):
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
                            "entry_id": hit["entry_id"],
                            "dictionary_value": hit["value"],
                            "match": hit["match"],
                            "kind": kind,
                            "source": hit["source"],
                            "detector_version": "prose-anti-junk-v0.1",
                        },
                        severity="ATTENTION",
                        confidence=1.0 if kind == "BANNED_TEMPLATE" else 0.75,
                        recommended_action=(
                            "Переформулировать мысль прямо и конкретно; не использовать шаблонную "
                            "нейросетевую/рекламную рамку."
                            if kind == "BANNED_TEMPLATE"
                            else "Проверить контекст: оставить слово только если его буквальный смысл необходим."
                        ),
                    )
                )
        return _CheckResult(
            findings=findings,
            metrics={
                "banned_template_hit_count": banned_count,
                "context_review_hit_count": review_count,
                "dictionary_entry_count": len(self.anti_junk.list_entries()),
            },
            output={
                "detector_version": "prose-anti-junk-v0.1",
                "claim": "dictionary/pattern quality signals only; no AI-authorship inference",
            },
        )

    def _execute_deterministic(
        self, spec: CheckSpec, snapshot: EvaluationSnapshotView
    ) -> _CheckResult:
        if spec.check_id == "deterministic.prose_anti_junk":
            return self._check_prose_anti_junk(snapshot)
        return super()._execute_deterministic(spec, snapshot)

    def run_deterministic_suite(self, book_id: str, snapshot_id: str) -> list[EvaluationRunView]:
        runs = super().run_deterministic_suite(book_id, snapshot_id)
        runs.append(self.run_check(book_id, snapshot_id, "deterministic.prose_anti_junk"))
        return runs
