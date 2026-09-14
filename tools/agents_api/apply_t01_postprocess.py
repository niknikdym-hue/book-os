#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def replace_once(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match in {rel}, got {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


QUALITY = "services/local-core/src/book_os_core/auto_book_quality.py"
FINALIZER = "services/local-core/src/book_os_core/auto_book_finalizer.py"
GATEWAY = "services/local-core/src/book_os_core/model_gateway.py"
QUALITY_TEST = "services/local-core/tests/test_auto_book_quality.py"
GATEWAY_TEST = "services/local-core/tests/test_model_gateway.py"

replace_once(
    QUALITY,
    '''    @staticmethod\n    def may_complete(\n        report: AutoQualityReport,\n        *,\n        current_master_hash: str | None = None,\n    ) -> bool:\n''',
    '''    @staticmethod\n    def may_admit_candidate(\n        report: AutoQualityReport,\n        *,\n        current_master_hash: str | None = None,\n    ) -> bool:\n        """Allow a HUMAN-review candidate with ATTENTION, never blockers or stale evidence."""\n        if current_master_hash is not None and report.master_hash != current_master_hash:\n            return False\n        if report.independent_review.master_hash != report.master_hash:\n            return False\n        if not report.independent_review.independent:\n            return False\n        if report.attempts_used > report.max_attempts:\n            return False\n        if report.finding_counts["BLOCKING"]:\n            return False\n        if report.independent_review.verdict == "BLOCKING":\n            return False\n        return True\n\n    @staticmethod\n    def may_complete(\n        report: AutoQualityReport,\n        *,\n        current_master_hash: str | None = None,\n    ) -> bool:\n''',
)

replace_once(
    FINALIZER,
    '''        if not self.quality.may_complete(report, current_master_hash=current_master_hash):\n            raise AutoBookGateError(\n                "final candidate quality review is stale, incomplete, or has unresolved findings"\n            )\n        return report\n''',
    '''        if not self.quality.may_admit_candidate(\n            report, current_master_hash=current_master_hash\n        ):\n            raise AutoBookGateError(\n                "final candidate quality review is stale, invalid, or has unresolved blockers"\n            )\n        return report\n''',
)

replace_once(
    FINALIZER,
    '''        if not self.quality.may_complete(\n            quality_report, current_master_hash=snapshot.manifest_hash\n        ):\n            raise AutoBookGateError(\n                "current exact-snapshot quality review is required before final candidate admission"\n            )\n        candidate = {\n''',
    '''        if not self.quality.may_admit_candidate(\n            quality_report, current_master_hash=snapshot.manifest_hash\n        ):\n            raise AutoBookGateError(\n                "current exact-snapshot blocker-free quality review is required before candidate admission"\n            )\n        candidate = {\n''',
)

replace_once(
    FINALIZER,
    '''            if not self.quality.may_complete(\n                quality_report, current_master_hash=snapshot.manifest_hash\n            ):\n                raise AutoBookGateError(\n                    "targeted change has unresolved independent-critique findings"\n                )\n            candidate = self._record_final_candidate(\n''',
    '''            if not self.quality.may_admit_candidate(\n                quality_report, current_master_hash=snapshot.manifest_hash\n            ):\n                raise AutoBookGateError(\n                    "targeted change has unresolved independent-critique blockers"\n                )\n            candidate = self._record_final_candidate(\n''',
)

replace_once(
    FINALIZER,
    '''        self._validated_candidate_quality(\n            payload,\n            current_master_hash=current_snapshot.manifest_hash,\n        )\n        master = self.literary.create_master(\n''',
    '''        quality_report = self._validated_candidate_quality(\n            payload,\n            current_master_hash=current_snapshot.manifest_hash,\n        )\n        if quality_report.finding_counts["ATTENTION"] and actor_kind != "HUMAN":\n            raise AutoBookGateError(\n                "unresolved ATTENTION findings require explicit HUMAN final acceptance"\n            )\n        master = self.literary.create_master(\n''',
)

replace_once(
    FINALIZER,
    '''        if not self.quality.may_complete(\n            quality_report, current_master_hash=snapshot.manifest_hash\n        ):\n            if correction_passes >= self._MAX_CORRECTION_PASSES:\n                raise AutoBookGateError(\n                    "bounded correction budget exhausted with unresolved release findings"\n                )\n            raise AutoBookGateError("independent correction did not clear release findings")\n        self.runtime.complete_stage(book_id, state.run_id, AutoBookStage.INDEPENDENT_CRITIQUE)\n''',
    '''        if not self.quality.may_complete(\n            quality_report, current_master_hash=snapshot.manifest_hash\n        ):\n            if not self.quality.may_admit_candidate(\n                quality_report, current_master_hash=snapshot.manifest_hash\n            ):\n                if correction_passes >= self._MAX_CORRECTION_PASSES:\n                    raise AutoBookGateError(\n                        "bounded correction budget exhausted with unresolved release blockers"\n                    )\n                raise AutoBookGateError(\n                    "independent correction did not clear release blockers"\n                )\n        self.runtime.complete_stage(book_id, state.run_id, AutoBookStage.INDEPENDENT_CRITIQUE)\n''',
)

replace_once(
    FINALIZER,
    '''        runtime = self.runtime.get(book_id, state.run_id)\n        if runtime.intent.final_human_acceptance_required:\n            self.runtime.set_stage(\n''',
    '''        runtime = self.runtime.get(book_id, state.run_id)\n        if (\n            runtime.intent.final_human_acceptance_required\n            or quality_report.finding_counts["ATTENTION"] > 0\n        ):\n            self.runtime.set_stage(\n''',
)

replace_once(
    GATEWAY,
    '''                output={\n                    "verdict": "PASS",\n                    "findings": [],\n                    "confidence": 0.75,\n                    "rationale": "Deterministic fake judge found no unresolved findings.",\n                },\n''',
    '''                output={\n                    "verdict": "ATTENTION",\n                    "findings": [\n                        {\n                            "location": "candidate:1",\n                            "evidence": "bounded synthetic signal",\n                            "recommended_action": "Human review.",\n                        }\n                    ],\n                    "confidence": 0.75,\n                    "rationale": "Deterministic fake judge fixture.",\n                },\n''',
)

replace_once(
    QUALITY_TEST,
    '''    assert AutoBookQualityEngine.may_complete(\n        report, current_master_hash=book.manifest_hash\n    ) is False\n\n\ndef test_stale_review_cannot_admit_a_changed_candidate() -> None:\n''',
    '''    assert AutoBookQualityEngine.may_complete(\n        report, current_master_hash=book.manifest_hash\n    ) is False\n    assert AutoBookQualityEngine.may_admit_candidate(\n        report, current_master_hash=book.manifest_hash\n    ) is True\n\n\ndef test_stale_review_cannot_admit_a_changed_candidate() -> None:\n''',
)

replace_once(
    QUALITY_TEST,
    '''    assert report.attempts_used == report.max_attempts\n    assert report.finding_counts == {"ATTENTION": 1, "BLOCKING": 0}\n    assert AutoBookQualityEngine.may_complete(\n        report, current_master_hash=book.manifest_hash\n    ) is False\n''',
    '''    assert report.attempts_used == report.max_attempts\n    assert report.finding_counts == {"ATTENTION": 1, "BLOCKING": 0}\n    assert AutoBookQualityEngine.may_complete(\n        report, current_master_hash=book.manifest_hash\n    ) is False\n    assert AutoBookQualityEngine.may_admit_candidate(\n        report, current_master_hash=book.manifest_hash\n    ) is True\n''',
)

replace_once(
    GATEWAY_TEST,
    '''    assert judge_result.output["verdict"] == "PASS"\n    assert judge_result.output["findings"] == []\n''',
    '''    assert judge_result.output["verdict"] == "ATTENTION"\n''',
)

print("T01 postprocess applied")
