import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ResearchPanel } from "./ResearchPanel";
import type { DraftRunView } from "./draftingTypes";
import type {
  ClaimView,
  EvidenceView,
  ResearchApi,
  ResearchCandidate,
  SourceView,
} from "./researchTypes";
import type { ChapterView, ProjectView } from "./types";

const chapter: ChapterView = {
  chapter_id: "01JCHAPTER000000000000000",
  ordinal: 1,
  working_title: "Evidence",
  architecture_role: "Explain evidence",
  workflow_state: "CONTRACT_APPROVED",
  chapter_contract: {
    entity_id: "01JCONTRACT00000000000000",
    revision_id: "01JCONTRACTREV00000000000",
    status: "APPROVED",
    authority_revision_id: "01JCONTRACTREV00000000000",
    authority_status: "APPROVED",
    content: { chapter_purpose: "Explain evidence" },
  },
};

const project: ProjectView = {
  book_id: "01JBOOK000000000000000000",
  working_title: "Research Book",
  mode: "BOOK_FROM_ZERO",
  domain: "BUSINESS_NONFICTION",
  primary_subtype: "Strategy",
  secondary_subtype: null,
  profile_version: "business-nonfiction-v0.1",
  workflow_stage: "WRITING",
  book_contract: null,
  architecture: null,
  chapters: [chapter],
};

const draft: DraftRunView = {
  task_id: "01JTASK0000000000000000000",
  run_id: "01JRUN00000000000000000000",
  task_status: "SUCCEEDED",
  run_status: "SUCCEEDED",
  provider: "openai",
  model: "writer",
  selection_mode: "AUTO",
  selection_scope: null,
  routing_rationale: "BOOK OS Auto routing for SECTION_DRAFT",
  prompt_id: "section_draft_v1",
  prompt_version: "1.0.0",
  prompt_hash: "a".repeat(64),
  input_revision_id: "01JINPUT00000000000000000",
  input_revision_hash: "b".repeat(64),
  unit_id: "01JUNIT0000000000000000000",
  revision_id: "01JDRAFTREV00000000000000",
  revision_hash: "c".repeat(64),
  revision_status: "DRAFT",
  text: "Evidence quality changes verification confidence.",
  notes: [],
  provider_run_id: "resp_test",
  usage: {},
  error_code: null,
  error_message: null,
};

const candidate: ResearchCandidate = {
  provider: "openalex",
  external_id: "W1",
  title: "Evidence Quality",
  authors: ["A. Researcher"],
  organization: null,
  publication_date: "2024-01-01",
  publication_year: 2024,
  doi: "10.9999/evidence.1",
  canonical_url: "https://doi.org/10.9999/evidence.1",
  container_title: "Evidence Journal",
  source_type: "article",
  abstract: null,
};

const source: SourceView = {
  source_id: "01JSOURCE0000000000000000",
  identifier: candidate.doi,
  title: candidate.title,
  authors: candidate.authors,
  organization: candidate.organization,
  publication_date: candidate.publication_date,
  publication_year: candidate.publication_year,
  doi: candidate.doi,
  url: candidate.canonical_url,
  source_type: candidate.source_type,
  provenance: { provider: candidate.provider, external_id: candidate.external_id },
  access_status: "METADATA_ONLY",
  rights_note: null,
  retrieved_at: "2026-08-25T00:00:00Z",
};

const claim: ClaimView = {
  claim_id: "01JCLAIM00000000000000000",
  book_id: project.book_id,
  chapter_id: chapter.chapter_id,
  unit_id: draft.unit_id,
  text: "Evidence quality changes verification confidence.",
  verification_state: "UNVERIFIED",
  risk_level: "MATERIAL",
  source_requirements: "Find direct support.",
  notes: null,
  created_at: "2026-08-25T00:00:00Z",
  updated_at: "2026-08-25T00:00:00Z",
};

const evidence: EvidenceView = {
  evidence_id: "01JEVIDENCE000000000000000",
  claim_id: claim.claim_id,
  source_id: source.source_id,
  stance: "SUPPORTS",
  locator: "abstract",
  excerpt: "Evidence quality is associated with verification confidence.",
  relevance_note: "Directly addresses the claim.",
  status: "PROPOSED",
  created_at: "2026-08-25T00:00:00Z",
};

const calls: Array<{ method: string; path: string; body?: unknown }> = [];

const fakeApi: ResearchApi = async function fakeApi<T>(method, path, body): Promise<T> {
  calls.push({ method, path, body });
  if (method === "GET" && path.includes("/claims")) return [claim] as T;
  if (method === "GET" && path.includes("/sources")) return [source] as T;
  if (method === "GET" && path.includes("/evidence")) return [evidence] as T;
  if (method === "POST" && path.endsWith("/research/search")) return [candidate] as T;
  if (method === "POST" && path.endsWith("/sources/import")) return source as T;
  if (method === "POST" && path.endsWith("/claims")) return claim as T;
  if (method === "POST" && path.endsWith("/evidence")) return evidence as T;
  return {} as T;
};

it("keeps research search/import/claim/evidence behind the local API boundary", async () => {
  render(
    <ResearchPanel
      project={project}
      chapter={chapter}
      latestDraft={draft}
      api={fakeApi}
    />,
  );

  fireEvent.change(screen.getByLabelText("Что ищем"), {
    target: { value: "evidence quality" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Найти источники" }));
  expect(await screen.findByText("Evidence Quality")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Сохранить источник" }));
  expect(await screen.findByText(/METADATA_ONLY/)).toBeInTheDocument();
  expect(calls.some((item) => item.path.endsWith("/research/search"))).toBe(true);
  expect(calls.some((item) => item.path.endsWith("/sources/import"))).toBe(true);
});
