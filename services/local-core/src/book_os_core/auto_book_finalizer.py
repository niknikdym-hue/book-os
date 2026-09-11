from __future__ import annotations

from html import escape as html_escape
from pathlib import Path
from typing import Any, cast
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import BaseModel, ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import AuthorityService, new_ulid
from .authority_types import JSONValue
from .auto_book import AutoBookGateError, AutoBookRunView
from .book_context import BookContextService
from .bookbench import BookBenchReport, BookBenchService
from .db import create_database
from .editorial import EditorialService
from .editorial_diagnostics import EditorialDiagnostics
from .literary_master import LiteraryMasterService
from .model_gateway import (
    AuthorityInputRef,
    ModelGateway,
    ModelOutputError,
    ModelTaskRequest,
    ReasoningEffort,
    SectionDraftOutput,
)
from .model_routing import ModelRoutingService
from .projects import ProjectService
from .prompts import PromptTemplate
from .series_production import ProductionCheckpointRequest, SeriesProductionService


AUTO_BOOK_FINAL_EDIT_V1 = PromptTemplate(
    prompt_id="auto_book_final_edit_v1",
    version="1.0.0",
    developer_text=(
        "You are the bounded BOOK OS final literary editor. Rewrite only the supplied current "
        "manuscript unit into publication-ready prose while preserving its substantive meaning and "
        "all supported facts. The approved Chapter Contract and Book Context are authoritative. "
        "Make every required claim clearly present, improve coherence, rhythm, transitions, "
        "specificity and density, remove filler and generic AI phrasing, and obey all style/prose "
        "prohibitions. Do not add unsupported facts, citations, studies, quotations, examples or "
        "claims. For a series, obey the Series Profile exclusions: never introduce material reserved "
        "for another volume and never copy examples, cases, metaphors, analogies, mechanisms, "
        "composition patterns or distinctive wording from another series book or style reference. "
        "Return only the complete revised manuscript unit as schema-valid text output."
    ),
)


class AutoBookFinalizationView(BaseModel):
    master_id: str
    master_manifest_hash: str
    bookbench_snapshot_id: str
    output_path: str | None
    requests_used: int
    authorized_cost_usd: float


class AutoBookFinalizer:
    _LITRES_FORBIDDEN = str.maketrans("", "", "ˊˈʻʼˋʹːˌ")

    def __init__(self, data_dir: Path, gateway: ModelGateway) -> None:
        self.data_dir = data_dir
        self.gateway = gateway
        self.projects = ProjectService(data_dir)
        self.contexts = BookContextService(data_dir)
        self.routing = ModelRoutingService(data_dir)
        self.editorial = EditorialService(data_dir)
        self.diagnostics = EditorialDiagnostics(data_dir, self.editorial)
        self.bookbench = BookBenchService(data_dir)
        self.literary = LiteraryMasterService(data_dir)
        self.series = SeriesProductionService(data_dir)

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    @staticmethod
    def _choice(
        state: AutoBookRunView,
    ) -> tuple[str | None, ReasoningEffort | None, str]:
        if state.model_choice == "AUTO":
            return None, None, "AUTO"
        if state.model_choice == "ASTRA_MEDIUM":
            return "gpt-6-astra", "medium", "MANUAL"
        if state.model_choice == "ASTRA_XHIGH":
            return "gpt-6-astra", "xhigh", "MANUAL"
        if state.model_choice == "SOL":
            return "gpt-5.6-sol", None, "MANUAL"
        return "gpt-6-astra", "high", "MANUAL"

    @staticmethod
    def _remaining_cap(state: AutoBookRunView) -> float:
        if state.requests_used >= state.max_requests:
            raise AutoBookGateError(
                "Auto Book request limit reached before the required final editorial pass"
            )
        remaining = state.max_total_cost_usd - state.authorized_cost_usd
        cap = min(state.max_cost_usd_per_request, remaining)
        if cap <= 0:
            raise AutoBookGateError(
                "Auto Book total cost authorization is exhausted before final editorial pass"
            )
        return cap

    @staticmethod
    def _consume(state: AutoBookRunView, cap: float) -> None:
        state.requests_used += 1
        state.authorized_cost_usd = round(state.authorized_cost_usd + cap, 6)

    def _book_context(self, book_id: str) -> dict[str, Any]:
        context = self.contexts.get_context(book_id)
        if not context.ready_for_planning:
            raise AutoBookGateError("final editorial pass requires the approved Book Context")
        return {
            "author_profile": (
                context.author_profile.model_dump(mode="json")
                if context.author_profile is not None
                else None
            ),
            "series_profile": (
                context.series_profile.model_dump(mode="json")
                if context.series_profile is not None
                else None
            ),
            "style_profile": (
                context.style_profile.model_dump(mode="json")
                if context.style_profile is not None
                else None
            ),
            "target_characters": context.target_characters,
            "min_characters": context.min_characters,
            "max_characters": context.max_characters,
            "include_bibliography": context.include_bibliography,
            "plan_illustrations": context.plan_illustrations,
        }

    def _resolve_model(
        self, book_id: str, state: AutoBookRunView
    ) -> tuple[str, ReasoningEffort | None, str, str | None, str]:
        model, effort, mode = self._choice(state)
        choice = self.routing.resolve(
            book_id,
            "SECTION_DRAFT",
            provider="openai",
            selection_mode=cast(Any, mode),
            selection_scope="OPERATION" if mode == "MANUAL" else None,
            model=model,
        )
        return (
            choice.model,
            effort if choice.model == "gpt-6-astra" else None,
            choice.selection_mode,
            choice.selection_scope,
            choice.rationale,
        )

    def _current_units(self, book_id: str) -> list[dict[str, Any]]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                rows = list(
                    connection.execute(
                        text(
                            "SELECT mu.unit_id,mu.chapter_id,mu.authority_entity_id,c.ordinal AS "
                            "chapter_ordinal,c.working_title,c.chapter_contract_entity_id "
                            "FROM manuscript_units mu JOIN chapters c ON c.chapter_id=mu.chapter_id "
                            "WHERE mu.book_id=:book_id AND c.workflow_state!='SUPERSEDED' "
                            "ORDER BY c.ordinal,mu.ordinal,mu.unit_id"
                        ),
                        {"book_id": book_id},
                    ).mappings()
                )
            return [dict(row) for row in rows]
        finally:
            engine.dispose()

    def _final_edit_unit(
        self,
        book_id: str,
        state: AutoBookRunView,
        unit: dict[str, Any],
        book_context: dict[str, Any],
    ) -> None:
        engine = self._engine(book_id)
        authority = AuthorityService(engine)
        try:
            entity_id = str(unit["authority_entity_id"])
            head = authority.get_head(entity_id)
            if head.status in {"APPROVED", "LOCKED"}:
                return
            revision = authority.get_revision(head.revision_id)
            content = cast(dict[str, Any], revision["content"])
            current_text = content.get("text")
            if not isinstance(current_text, str) or not current_text.strip():
                raise AutoBookGateError(f"manuscript unit {unit['unit_id']} has no editable text")

            contract_entity = unit.get("chapter_contract_entity_id")
            if not isinstance(contract_entity, str) or not contract_entity:
                raise AutoBookGateError(
                    f"chapter {unit['chapter_ordinal']} has no Chapter Contract for final edit"
                )
            contract_head = authority.get_head(contract_entity)
            if contract_head.status not in {"APPROVED", "LOCKED"}:
                raise AutoBookGateError(
                    f"chapter {unit['chapter_ordinal']} contract is not approved for final edit"
                )
            contract_revision = authority.get_revision(contract_head.revision_id)
            contract = cast(dict[str, Any], contract_revision["content"])

            cap = self._remaining_cap(state)
            model, effort, selection_mode, selection_scope, rationale = self._resolve_model(
                book_id, state
            )
            task_id = new_ulid()
            result = self.gateway.generate(
                ModelTaskRequest(
                    task_id=task_id,
                    task_type="SECTION_DRAFT",
                    role="WRITER",
                    provider="openai",
                    model=model,
                    prompt_id=AUTO_BOOK_FINAL_EDIT_V1.prompt_id,
                    prompt_version=AUTO_BOOK_FINAL_EDIT_V1.version,
                    prompt_hash=AUTO_BOOK_FINAL_EDIT_V1.prompt_hash,
                    section_objective=(
                        f"Final publication edit of chapter {unit['chapter_ordinal']}: "
                        f"{unit['working_title']}. Preserve meaning and supported facts; make the "
                        "approved chapter function explicit and produce only finished book prose."
                    ),
                    authority_inputs=[
                        AuthorityInputRef(
                            revision_id=head.revision_id,
                            revision_hash=head.revision_hash,
                            entity_type="manuscript.unit",
                        ),
                        AuthorityInputRef(
                            revision_id=contract_head.revision_id,
                            revision_hash=contract_head.revision_hash,
                            entity_type="chapter.contract",
                        ),
                    ],
                    authoritative_context={
                        "current_manuscript_text": current_text,
                        "chapter_contract": contract,
                        "book_context": book_context,
                    },
                    task_payload={
                        "auto_book_run_id": state.run_id,
                        "selection_mode": selection_mode,
                        "selection_scope": selection_scope,
                        "routing_rationale": rationale,
                        "final_editorial_pass": True,
                    },
                    reasoning_effort=effort,
                    max_output_tokens=12_000,
                    max_cost_usd=cap,
                ),
                AUTO_BOOK_FINAL_EDIT_V1,
            )
            self._consume(state, cap)
            try:
                output = SectionDraftOutput.model_validate(result.output)
            except ValidationError as exc:
                raise ModelOutputError(
                    "final editorial output failed SectionDraft schema validation"
                ) from exc
            latest = authority.get_head(entity_id)
            if latest.revision_id != head.revision_id or latest.revision_hash != head.revision_hash:
                raise AutoBookGateError("manuscript authority changed during final editorial pass")

            proposed_payload = cast(dict[str, JSONValue], dict(content))
            proposed_payload["text"] = output.text
            proposed_payload["notes"] = cast(list[JSONValue], output.notes)
            proposal_id = authority.create_proposal(
                entity_id=entity_id,
                base_revision_id=head.revision_id,
                base_revision_hash=head.revision_hash,
                proposed_payload=proposed_payload,
                schema_name=cast(str, revision["schema_name"]),
                schema_version=cast(str, revision["schema_version"]),
                rationale=(
                    f"Owner-preauthorized final editorial pass for Auto Book run {state.run_id}; "
                    f"model={model}; prompt={AUTO_BOOK_FINAL_EDIT_V1.prompt_hash}"
                ),
                actor=f"model:{model}",
                origin="AI_ASSISTED",
                task_id=task_id,
                input_revision_ids=(contract_head.revision_id,),
            )
            authority.accept_proposal(
                proposal_id,
                actor="OWNER",
                actor_kind="HUMAN",
                reason=(
                    f"Owner pre-authorized final editorial acceptance for Auto Book run {state.run_id}"
                ),
                gates={
                    "owner_auto_book_authorization": True,
                    "auto_book_run_id": state.run_id,
                    "final_editorial_pass": True,
                    "model": model,
                    "prompt_hash": AUTO_BOOK_FINAL_EDIT_V1.prompt_hash,
                },
            )
        finally:
            engine.dispose()

    def _run_editorial_gates(self, book_id: str) -> None:
        project = self.projects.get_project(book_id)
        for chapter in project.chapters:
            self.diagnostics.run_developmental(book_id, chapter.chapter_id)
        self.diagnostics.run_cross_book(book_id)
        self.diagnostics.run_fact_checker(book_id)
        blocking = [
            finding
            for finding in self.editorial.list_findings(book_id, status="OPEN")
            if finding.severity in {"MAJOR", "CRITICAL"}
        ]
        if blocking:
            summary = "; ".join(
                f"{item.role}/{item.category}: {item.diagnosis}" for item in blocking[:6]
            )
            raise AutoBookGateError(
                "final editorial review requires rework before Literary Master: " + summary
            )

    def _run_bookbench(self, book_id: str) -> BookBenchReport:
        snapshot = self.bookbench.create_snapshot(book_id, scope="BOOK")
        runs = self.bookbench.run_deterministic_suite(book_id, snapshot.snapshot_id)
        failed = [run for run in runs if run.status != "SUCCEEDED"]
        if failed:
            raise AutoBookGateError(
                "BookBench deterministic suite failed: " + ", ".join(run.check_id for run in failed)
            )
        report = self.bookbench.report(book_id, snapshot.snapshot_id)
        if not report.current:
            raise AutoBookGateError("BookBench snapshot became stale during final review")
        if report.blocking_dimensions:
            raise AutoBookGateError(
                "BookBench has BLOCKING dimensions: " + ", ".join(report.blocking_dimensions)
            )
        return report

    def _record_adversarial_review(self, book_id: str, report: BookBenchReport) -> None:
        findings: list[dict[str, Any]] = []
        attention = False
        blocking = False
        for dimension in report.dimensions:
            if dimension.state == "PASS":
                continue
            if dimension.state == "BLOCKING":
                blocking = True
            else:
                attention = True
            findings.append(
                {
                    "dimension": dimension.dimension,
                    "state": dimension.state,
                    "finding_ids": [item.finding_id for item in dimension.findings],
                    "categories": [item.category for item in dimension.findings],
                    "run_ids": dimension.run_ids,
                }
            )
        status = "BLOCKING" if blocking else "ATTENTION" if attention else "PASS"
        checkpoint = self.series.record_checkpoint(
            book_id,
            ProductionCheckpointRequest(
                kind="ADVERSARIAL_REVIEW",
                status=status,
                findings=findings,
                actor_kind="SYSTEM",
                actor="system:auto-book-independent-release-review",
                executor_identity="bookbench-deterministic-independent-auditor-v1",
                snapshot_hash=report.snapshot_hash,
                independent=True,
            ),
        )
        if checkpoint.status == "BLOCKING":
            raise AutoBookGateError(
                "independent Adversarial Review found BLOCKING release issues"
            )
        ready, blockers = self.series.adversarial_review_gate(book_id)
        if not ready:
            raise AutoBookGateError(
                "independent Adversarial Review gate failed: " + "; ".join(blockers)
            )

    @classmethod
    def _clean_litres_text(cls, value: str) -> str:
        cleaned = value.translate(cls._LITRES_FORBIDDEN)
        cleaned = "".join(ch for ch in cleaned if not (0x1F000 <= ord(ch) <= 0x1FAFF))
        return cleaned.replace("\r\n", "\n").replace("\r", "\n").strip()

    @staticmethod
    def _xml_text(value: str) -> str:
        return html_escape(value, quote=False)

    @classmethod
    def _docx_body(cls, manuscript: str) -> list[str]:
        body: list[str] = []
        paragraph_lines: list[str] = []

        def flush() -> None:
            if not paragraph_lines:
                return
            value = cls._clean_litres_text(" ".join(paragraph_lines))
            paragraph_lines.clear()
            if value:
                body.append(
                    f'<w:p><w:r><w:t xml:space="preserve">{cls._xml_text(value)}</w:t></w:r></w:p>'
                )

        for raw_line in manuscript.splitlines():
            line = raw_line.strip()
            if line.startswith("## "):
                flush()
                title = cls._clean_litres_text(line[3:])
                body.append(
                    '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
                    f"<w:r><w:t>{cls._xml_text(title)}</w:t></w:r></w:p>"
                )
            elif line.startswith("# "):
                flush()
                title = cls._clean_litres_text(line[2:])
                body.append(
                    '<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr>'
                    f"<w:r><w:t>{cls._xml_text(title)}</w:t></w:r></w:p>"
                )
            elif not line:
                flush()
            else:
                paragraph_lines.append(line)
        flush()
        return body

    def _export_litres_docx(self, book_id: str, master_id: str) -> str:
        master = self.literary.get_master(book_id, master_id)
        canonical = self.literary._canonical_bytes_from_master(master).decode("utf-8")
        body_parts = self._docx_body(canonical)
        if not body_parts:
            raise AutoBookGateError("Literary Master contains no exportable manuscript text")

        document_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body>"
            + "".join(body_parts)
            + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" '
            'w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>'
        )
        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
            '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/>'
            '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
            '<w:rPr><w:b/><w:sz w:val="40"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>'
            '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
            '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style></w:styles>'
        )
        content_types = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            "</Types>"
        )
        root_rels = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>"
        )
        document_rels = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>"
        )

        relative_path = f"exports/{master_id}/litres-ready.docx"
        output = self.projects.projects_dir / book_id / relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("_rels/.rels", root_rels)
            archive.writestr("word/document.xml", document_xml)
            archive.writestr("word/styles.xml", styles_xml)
            archive.writestr("word/_rels/document.xml.rels", document_rels)
        payload = output.read_bytes()
        self.literary._record_export(
            book_id,
            master_id,
            format_name="LITRES_DOCX",
            relative_path=relative_path,
            payload=payload,
        )
        return str(output)

    def finalize(
        self,
        book_id: str,
        state: AutoBookRunView,
        *,
        prepare_litres_docx: bool,
    ) -> AutoBookFinalizationView:
        book_context = self._book_context(book_id)
        units = self._current_units(book_id)
        if not units:
            raise AutoBookGateError("final editorial pass requires manuscript units")
        for unit in units:
            self._final_edit_unit(book_id, state, unit, book_context)

        self._run_editorial_gates(book_id)
        report = self._run_bookbench(book_id)
        self._record_adversarial_review(book_id, report)

        master = self.literary.create_master(
            book_id,
            human_actor=f"OWNER Auto Book {state.run_id}",
        )
        output_path = (
            self._export_litres_docx(book_id, master.master_id) if prepare_litres_docx else None
        )
        return AutoBookFinalizationView(
            master_id=master.master_id,
            master_manifest_hash=master.manifest_hash,
            bookbench_snapshot_id=report.snapshot_id,
            output_path=output_path,
            requests_used=state.requests_used,
            authorized_cost_usd=state.authorized_cost_usd,
        )
