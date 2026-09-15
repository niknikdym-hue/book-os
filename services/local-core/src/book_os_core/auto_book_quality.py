from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .auto_book_exports import StructuredBookMaster


QualitySeverity = Literal["ATTENTION", "BLOCKING"]
ReviewVerdict = Literal["PASS", "ATTENTION", "BLOCKING"]


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
    verdict: ReviewVerdict
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    findings: list[AutoQualityFinding]


class AutoQualityReport(BaseModel):
    master_hash: str
    claim_coverage: list[ClaimCoverageItem]
    findings: list[AutoQualityFinding]
    finding_counts: dict[QualitySeverity, int]
    independent_review: IndependentBookReview
    status: Literal["PASS", "REWORK"]
    attempts_used: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=2, ge=1)

    @model_validator(mode="after")
    def validate_report_evidence(self) -> AutoQualityReport:
        expected_counts: dict[QualitySeverity, int] = {
            "ATTENTION": sum(item.severity == "ATTENTION" for item in self.findings),
            "BLOCKING": sum(item.severity == "BLOCKING" for item in self.findings),
        }
        if self.finding_counts != expected_counts:
            raise ValueError("finding counts must match the exact unresolved findings")
        if self.independent_review.master_hash != self.master_hash:
            raise ValueError("independent review must match the report exact snapshot")
        if self.independent_review.findings != self.findings:
            raise ValueError("independent review findings must match the report findings")
        if self.attempts_used > self.max_attempts:
            raise ValueError("correction attempts exceed the bounded correction budget")
        expected_status: Literal["PASS", "REWORK"] = (
            "REWORK" if self.findings or self.independent_review.verdict != "PASS" else "PASS"
        )
        if self.status != expected_status:
            raise ValueError("quality status must reflect every unresolved review finding")
        return self


class AutoBookQualityEngine:
    """Deterministic whole-book coverage complement to Editorial and BookBench.

    The engine intentionally does not pretend to be a literary model. It catches provable
    coverage failures and creates an exact-snapshot independent-review record. Substantive model
    criticism can add findings, but cannot silently erase these gates.

    Material-claim detection deliberately stays conservative: it looks for explicit external-world
    signals (quantification, research/data language, dated historical assertions, attribution,
    legal/regulatory language, consensus language and time-sensitive platform/market/technology
    assertions). This avoids treating every authorial causal explanation as a sourced fact while
    ensuring those high-risk claim classes cannot silently bypass the evidence ledger.
    """

    _FACT_PATTERN = re.compile(
        r"(?P<sentence>[^.!?\n]*(?:"
        r"\d[\d\s.,]*\s*(?:%|процент|руб|дн|год|месяц)|"
        r"согласно\s+(?:исследованию|данным|закону|правилам)|"
        r"(?:исследовани[ея]|данные|опрос|наблюдени[ея])\s+"
        r"(?:показыва\w*|свидетельств\w*|выяв\w*|обнаруж\w*)|"
        r"(?:исследования|данные|наблюдения)[^.!?\n]{0,120}"
        r"(?:приводит|влияет|вызывает|снижает|повышает)|"
        r"(?:в\s+\d{4}\s+году|впервые\s+в\s+\d{4}|с\s+\d{4}\s+года)|"
        r"(?:по\s+словам|по\s+оценке|как\s+утверждает|как\s+сообщает)\s+"
        r"[^.!?\n]{2,100}|"
        r"(?:закон|правила|требования|регламент)[^.!?\n]{0,100}"
        r"(?:требу\w*|запрещ\w*|разреш\w*|обязыва\w*)|"
        r"(?:консенсус|эксперты\s+(?:сходятся|согласны)|общепринято)"
        r"[^.!?\n]{0,100}|"
        r"(?:рынок|платформа|алгоритм|технология)[^.!?\n]{0,100}"
        r"(?:сейчас|сегодня|в\s+настоящее\s+время|использует|требует|работает|изменил|изменяет)"
        r")[^.!?\n]*[.!?])",
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
    def _claims_same_fact(cls, current: str, registered: str) -> bool:
        return cls._normalized(current) == cls._normalized(registered)

    @classmethod
    def material_claims(cls, text: str) -> list[str]:
        """Extract conservative material-claim candidates from exact manuscript prose."""

        claims: list[str] = []
        seen: set[str] = set()
        for match in cls._FACT_PATTERN.finditer(text):
            claim = match.group("sentence").strip()
            normalized = cls._normalized(claim)
            if normalized and normalized not in seen:
                seen.add(normalized)
                claims.append(claim)
        return claims

    def _claim_coverage(
        self,
        master: StructuredBookMaster,
        registered_claims: dict[str, bool],
    ) -> tuple[list[ClaimCoverageItem], list[AutoQualityFinding]]:
        coverage: list[ClaimCoverageItem] = []
        findings: list[AutoQualityFinding] = []
        normalized_ledger = [(claim, current) for claim, current in registered_claims.items()]
        for chapter in master.chapters:
            text = " ".join(chapter.paragraphs)
            for claim in self.material_claims(text):
                ledger_match = next(
                    (
                        (candidate, current)
                        for candidate, current in normalized_ledger
                        if self._claims_same_fact(claim, candidate)
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
        critic_verdict: ReviewVerdict | None = None,
        critic_rationale: str | None = None,
        critic_confidence: float | None = None,
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
        counts: dict[QualitySeverity, int] = {
            "ATTENTION": sum(finding.severity == "ATTENTION" for finding in findings),
            "BLOCKING": sum(finding.severity == "BLOCKING" for finding in findings),
        }
        blocking = [finding for finding in findings if finding.severity == "BLOCKING"]
        attention = [finding for finding in findings if finding.severity == "ATTENTION"]
        if blocking:
            summary = (
                f"Независимый разбор exact snapshot {master.manifest_hash[:12]} нашёл "
                f"{len(blocking)} блокирующих замечаний. Нужна адресная доработка и повторная "
                "проверка затронутых мест и сквозных инвариантов."
            )
        elif attention:
            summary = (
                "Независимый разбор exact snapshot "
                f"{master.manifest_hash[:12]} сохранил {len(attention)} незакрытых замечаний "
                "ATTENTION. Нужна адресная доработка и повторная проверка exact snapshot до "
                "допуска к финальному кандидату."
            )
        else:
            summary = (
                f"Независимый разбор exact snapshot {master.manifest_hash[:12]} не нашёл "
                "детерминированных блокирующих дефектов; это не заменяет человеческую оценку "
                "литературного качества и сравнительный реальный trial."
            )
        effective_verdict: ReviewVerdict = critic_verdict or (
            "BLOCKING" if blocking else "ATTENTION" if attention else "PASS"
        )
        review = IndependentBookReview(
            master_hash=master.manifest_hash,
            reviewer_identity=reviewer_identity,
            writer_identity=writer_identity,
            independent=True,
            summary=summary,
            verdict=effective_verdict,
            rationale=critic_rationale or summary,
            confidence=1.0 if critic_confidence is None else critic_confidence,
            findings=findings,
        )
        return AutoQualityReport(
            master_hash=master.manifest_hash,
            claim_coverage=coverage,
            findings=findings,
            finding_counts=counts,
            independent_review=review,
            status="REWORK" if findings or effective_verdict != "PASS" else "PASS",
            attempts_used=attempts_used,
            max_attempts=max_attempts,
        )

    @staticmethod
    def may_admit_candidate(
        report: AutoQualityReport,
        *,
        current_master_hash: str | None = None,
    ) -> bool:
        """Allow a HUMAN-review candidate with ATTENTION, never blockers or stale evidence."""
        if current_master_hash is not None and report.master_hash != current_master_hash:
            return False
        if report.independent_review.master_hash != report.master_hash:
            return False
        if not report.independent_review.independent:
            return False
        if report.attempts_used > report.max_attempts:
            return False
        if report.finding_counts["BLOCKING"]:
            return False
        if report.independent_review.verdict == "BLOCKING":
            return False
        return True

    @staticmethod
    def may_complete(
        report: AutoQualityReport,
        *,
        current_master_hash: str | None = None,
    ) -> bool:
        if report.status != "PASS":
            return False
        if current_master_hash is not None and report.master_hash != current_master_hash:
            return False
        if report.independent_review.master_hash != report.master_hash:
            return False
        if not report.independent_review.independent:
            return False
        if report.independent_review.verdict != "PASS":
            return False
        if report.attempts_used > report.max_attempts:
            return False
        return not report.findings
