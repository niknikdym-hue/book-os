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
  citation_count: 10,
  provider_url: "https://openalex.org/W1",
  raw_identifiers: { openalex: "W1" },
};

const source: SourceView = {
  source_id: "01JSOURCE00000000000000000",
  canonical_key: "doi:10.9999/evidence.1",
  source_type: "article",
  title: "Evidence Quality",
  authors: ["A. Researcher"],
  organization: null,
  publication_date: "2024-01-01",
  publication_year: 2024,
  doi: "10.9999/evidence.1",
  canonical_url: "https://doi.org/10.9999/evidence.1",
  container_title: "Evidence Journal",
  abstract: null,
  citation_count: 10,
  primary_secondary: "UNCLASSIFIED",
  access_status: "METADATA_ONLY",
  identifiers: { openalex: ["W1"] },
};

let claim: ClaimView | null = null;
let evidence: EvidenceView[] = [];

const api: ResearchApi = async function api<T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
): Promise<T> {
  if (method === "GET" && path.includes("/drafts")) return [draft] as T;
  if (method === "GET" && path.includes("/claims?") ) return (claim ? [claim] : []) as T;
  if (method === "GET" && path.includes("/evidence")) return evidence as T;
  if (method === "POST" && path.endsWith("/claims")) {
    const payload = body as Record<string, unknown>;
    claim = {
      claim_id: "01JCLAIM000000000000000000",
      book_id: project.book_id,
      chapter_id: chapter.chapter_id,
      unit_id: String(payload.unit_id),
      manuscript_revision_id: String(payload.manuscript_revision_id),
      manuscript_revision_hash: String(payload.manuscript_revision_hash),
      normalized_text: String(payload.normalized_text),
      claim_type: String(payload.claim_type),
      materiality: "HIGH",
      required_evidence_level: "INSPECTED_SOURCE",
      verification_state: "UNREVIEWED",
      evidence_count: 0,
      created_at: "2026-08-25T00:00:00Z",
      updated_at: "2026-08-25T00:00:00Z",
    };
    return claim as T;
  }
  if (method === "POST" && path.endsWith("/research/search")) return [candidate] as T;
  if (method === "POST" && path.endsWith("/sources/import")) return source as T;
  if (method === "POST" && path.includes("/sources/") && path.endsWith("/access")) {
    return { ...source, access_status: "FULL_SOURCE_INSPECTED" } as T;
  }
  if (method === "POST" && path.endsWith("/evidence")) {
    const item: EvidenceView = {
      evidence_id: "01JEVIDENCE000000000000000",
      claim_id: claim?.claim_id ?? "",
      source_id: source.source_id,
      relationship: "SUPPORTS",
      pointer: "Section 2",
      note: "Direct support",
      strength: "MODERATE",
      limitations: "",
      actor: "OWNER",
      status: "ACTIVE",
      supersedes_evidence_id: null,
      created_at: "2026-08-25T00:00:00Z",
    };
    evidence = [item];
    if (claim) claim = { ...claim, verification_state: "SUPPORTED", evidence_count: 1 };
    return item as T;
  }
  throw new Error(`unexpected API call: ${method} ${path}`);
};

it("runs Claim → Source → Evidence and makes verification state visible", async () => {
  claim = null;
  evidence = [];
  render(<ResearchPanel project={project} chapter={chapter} api={api} />);

  expect(await screen.findByText("Exact manuscript revision")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Material claim"), {
    target: { value: "Evidence quality changes verification confidence." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Add Claim" }));
  expect(await screen.findByText(/UNREVIEWED · Evidence quality/)).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Research query"), {
    target: { value: "evidence quality" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Search metadata" }));
  expect(await screen.findByText("Evidence Quality")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Add Source metadata" }));
  expect(await screen.findByText(/Source status:/)).toBeInTheDocument();
  expect(screen.getByText("METADATA_ONLY")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Inspection note"), {
    target: { value: "Inspected Section 2 in the source." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Mark source inspected" }));
  expect(await screen.findByText("FULL_SOURCE_INSPECTED")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Evidence relationship"), {
    target: { value: "SUPPORTS" },
  });
  fireEvent.change(screen.getByLabelText("Evidence locator / pointer"), {
    target: { value: "Section 2" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Add Evidence" }));
  expect(await screen.findByText(/SUPPORTED · Evidence quality/)).toBeInTheDocument();
  const supportLabel = screen
    .getAllByText("SUPPORTS")
    .find((element) => element.tagName === "STRONG");
  expect(supportLabel?.parentElement).toHaveTextContent("SUPPORTS · Section 2 · ACTIVE");
});
