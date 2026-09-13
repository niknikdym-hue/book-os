from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Literal

from pydantic import BaseModel, Field

from .auto_book_exports import StructuredBookMaster


QualitySeverity = Literal["ATTENTION", "BLOCKING"]


class AutoQualityFinding(BaseModel):
    code: str
    severity: QualitySeverity
    location: str
    evidence: str
    required_action: str


class ClaimCoverageItem(BaseModel):
    claim_text: str
    chapter_id: str
    registered: bool
    current_evidence: bool


class IndependentBookReview(BaseModel):
    master_hash: str = Field(min_length=64, max_length=64)
    reviewer_identity: str = Field(min_length=1, max_length=255)
    writer_identity: str = Field(min_length=1, max_length=255)
    independent: bool
    summary: str = Field(min_length=40)
    findings: list[AutoQualityFinding]


class AutoQualityReport(BaseModel):
    master_hash: str
    claim_coverage: list[ClaimCoverageItem]
    findings: list[AutoQualityFinding]
    independent_review: IndependentBookReview
    status: Literal["PASS", "REWORK"]
    attempts_used: int = 0
    max_attempts: int = 2


class AutoBookQualityEngine:
    """Deterministic whole-book coverage complement to Editorial and BookBench.

    The engine intentionally does not pretend to be a literary model.  It catches provable
    coverage failures and creates an exact-snapshot independent-review record.  Substantive model
    criticism can add findings, but cannot silently erase these gates.
    """

    _FACT_PATTERN = re.compile(
        r"(?P<sentence>[^.!?\n]*(?:\d[\d\s.,]*\s*(?:%|процент|руб|дн|год|месяц)|"
        r"согласно\s+(?:исследованию|данным)|исследовани[ея]\s+показыва)[^.!?\n]*[.!?])",
        re.IGNORECASE,
    )
    _MECHANISM_PATTERN = re.compile(r"\b(?:механизм|правило|матрица|модель|алгоритм)\b", re.I)
    _QUANTIFIED_PATTERN = re.compile(
        r"(?P<subject>[А-ЯЁA-Z][^.!?\n:]{2,80}?)\s+(?:составляет|равен|равна|равно)\s+"
        r"(?P<value>\d[\d\s.,]*)",
        re.IGNORECASE,
    )

    @staticmethod
    def _normalized(value: str) -> str:
        return " ".join(re.findall(r"[а-яёa-z0-9]+", value.casefold()))

    @classmethod
    def _claim_shape(cls, value: str) -> str:
        return re.sub(r"\b\d+(?:[.,]\d+)?\b", "#", cls._normalized(value))

    def _claim_coverage(
        self,
        master: StructuredBookMaster,
        registered_claims: dict[str, bool],
    ) -> tuple[list[ClaimCoverageItem], list[AutoQualityFinding]]:
        coverage: list[ClaimCoverageItem] = []
        findings: list[AutoQualityFinding] = []
        normalized_ledger = [
            (self._normalized(claim), self._claim_shape(claim), current)
            for claim, current in registered_claims.items()
        ]
        for chapter in master.chapters:
            text = " ".join(chapter.paragraphs)
            for match in self._FACT_PATTERN.finditer(text):
                claim = match.group("sentence").strip()
                normalized = self._normalized(claim)
                ledger_match = next(
                    (
                        (candidate, current)
                        for candidate, shape, current in normalized_ledger
                        if candidate
                        and (
                            candidate in normalized
                            or normalized in candidate
                            or shape == self._claim_shape(claim)
                        )
                    ),
                    None,
                )
                registered = ledger_match is not None
                current = bool(ledger_match and ledger_match[1])
                coverage.append(
                    ClaimCoverageItem(
                        claim_text=claim,
                        chapter_id=chapter.chapter_id,
                        registered=registered,
                        current_evidence=current,
                    )
                )
                if not registered:
                    findings.append(
                        AutoQualityFinding(
                            code="UNREGISTERED_MATERIAL_CLAIM",
                            severity="BLOCKING",
                            location=f"chapter:{chapter.chapter_id}",
                            evidence=claim,
                            required_action=(
                                "Register and verify the claim, qualify it honestly, or remove it"
                            ),
                        )
                    )
                elif not current:
                    findings.append(
                        AutoQualityFinding(
                            code="STALE_CLAIM_EVIDENCE",
                            severity="BLOCKING",
                            location=f"chapter:{chapter.chapter_id}",
                            evidence=claim,
                            required_action="Re-check evidence against the exact current text revision",
                        )
                    )
        return coverage, findings

    def _cross_book_findings(self, master: StructuredBookMaster) -> list[AutoQualityFinding]:
        findings: list[AutoQualityFinding] = []
        paragraph_locations: dict[str, list[str]] = defaultdict(list)
        quantified: dict[str, list[tuple[str, str]]] = defaultdict(list)
        mechanism_terms: Counter[str] = Counter()
        for chapter in master.chapters:
            for paragraph_index, paragraph in enumerate(chapter.paragraphs, start=1):
                normalized = self._normalized(paragraph)
                if len(normalized) >= 100:
                    paragraph_locations[normalized].append(
                        f"chapter:{chapter.chapter_id}:paragraph:{paragraph_index}"
                    )
                for match in self._QUANTIFIED_PATTERN.finditer(paragraph):
                    subject = self._normalized(match.group("subject"))
                    value = self._normalized(match.group("value"))
                    quantified[subject].append((value, chapter.chapter_id))
                if self._MECHANISM_PATTERN.search(paragraph):
                    mechanism_terms.update(re.findall(r"\b[а-яёa-z]{6,}\b", normalized))

        for paragraph, locations in paragraph_locations.items():
            chapters = {location.split(":")[1] for location in locations}
            if len(chapters) > 1:
                findings.append(
                    AutoQualityFinding(
                        code="DISTANT_PARAGRAPH_REPEAT",
                        severity="BLOCKING",
                        location=", ".join(locations),
                        evidence=paragraph[:240],
                        required_action="Keep the mechanism once and give each chapter a distinct job",
                    )
                )
        for subject, values in quantified.items():
            distinct_values = {value for value, _ in values}
            chapters = {chapter for _, chapter in values}
            if len(distinct_values) > 1 and len(chapters) > 1:
                findings.append(
                    AutoQualityFinding(
                        code="DISTANT_QUANTIFIED_CONTRADICTION",
                        severity="BLOCKING",
                        location=", ".join(sorted(f"chapter:{value}" for value in chapters)),
                        evidence=f"{subject}: {', '.join(sorted(distinct_values))}",
                        required_action="Resolve the contradiction or state the different conditions",
                    )
                )
        return findings

    def review(
        self,
        master: StructuredBookMaster,
        *,
        registered_claims: dict[str, bool] | None = None,
        writer_identity: str,
        reviewer_identity: str,
        additional_findings: list[AutoQualityFinding] | None = None,
        attempts_used: int = 0,
        max_attempts: int = 2,
    ) -> AutoQualityReport:
        if reviewer_identity.strip().casefold() == writer_identity.strip().casefold():
            raise ValueError("independent reviewer must not be the writer")
        coverage, claim_findings = self._claim_coverage(master, registered_claims or {})
        findings = [
            *claim_findings,
            *self._cross_book_findings(master),
            *(additional_findings or []),
        ]
        blocking = [finding for finding in findings if finding.severity == "BLOCKING"]
        if blocking:
            summary = (
                f"Независимый разбор exact snapshot {master.manifest_hash[:12]} нашёл "
                f"{len(blocking)} блокирующих замечаний. Нужна адресная доработка и повторная "
                "проверка затронутых мест и сквозных инвариантов."
            )
        else:
            summary = (
                f"Независимый разбор exact snapshot {master.manifest_hash[:12]} не нашёл "
                "детерминированных блокирующих дефектов; это не заменяет человеческую оценку "
                "литературного качества и сравнительный реальный trial."
            )
        review = IndependentBookReview(
            master_hash=master.manifest_hash,
            reviewer_identity=reviewer_identity,
            writer_identity=writer_identity,
            independent=True,
            summary=summary,
            findings=findings,
        )
        return AutoQualityReport(
            master_hash=master.manifest_hash,
            claim_coverage=coverage,
            findings=findings,
            independent_review=review,
            status="REWORK" if blocking else "PASS",
            attempts_used=attempts_used,
            max_attempts=max_attempts,
        )

    @staticmethod
    def may_complete(report: AutoQualityReport) -> bool:
        if report.status != "PASS":
            return False
        return not any(finding.severity == "BLOCKING" for finding in report.findings)
