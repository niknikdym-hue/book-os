import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { EditorialPanel } from "./EditorialPanel";
import type {
  DecisionResult,
  EditorialApi,
  FindingView,
  InboxItem,
  ProposalView,
} from "./editorialTypes";
import type { ChapterView, ProjectView } from "./types";

const chapter: ChapterView = {
  chapter_id: "01JCHAPTER000000000000000",
  ordinal: 1,
  working_title: "Decision Loop",
  architecture_role: "Exercise editorial control",
  workflow_state: "CONTRACT_APPROVED",
  chapter_contract: null,
};

const project: ProjectView = {
  book_id: "01JBOOK000000000000000000",
  working_title: "Editorial Book",
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

const finding: FindingView = {
  finding_id: "01JFINDING000000000000000",
  run_id: null,
  book_id: project.book_id,
  role: "LITERARY_EDITOR",
  category: "BOUNDED_REWRITE",
  target_kind: "MANUSCRIPT_UNIT",
  target_entity_id: "01JENTITY0000000000000000",
  chapter_id: chapter.chapter_id,
  unit_id: "01JUNIT0000000000000000000",
  base_revision_id: "01JREVISION000000000000000",
  base_revision_hash: "a".repeat(64),
  diagnosis: "This current passage needs one bounded editorial revision.",
  why: "The material change must be reviewed against the exact current revision.",
  evidence: { source: "fixture" },
  severity: "MAJOR",
  confidence: 0.94,
  expected_effect: "Improve clarity without silent mutation.",
  risks: "Meaning could drift if accepted blindly.",
  actor: "OWNER",
  actor_kind: "HUMAN",
  status: "OPEN",
  created_at: "2026-08-26T10:00:00Z",
  resolved_at: null,
};

const proposal: ProposalView = {
  proposal_id: "01JPROPOSAL00000000000000",
  finding_id: finding.finding_id,
  status: "OPEN",
  stale: false,
  base_revision_id: finding.base_revision_id,
  base_revision_hash: finding.base_revision_hash,
  proposed_content_hash: "b".repeat(64),
  rationale: "Bounded rewrite after review.",
  proposed_text: "A revised passage that only becomes current after human acceptance.",
  diff: "--- current\n+++ proposed\n-old passage\n+A revised passage that only becomes current after human acceptance.\n",
  created_at: "2026-08-26T10:01:00Z",
};

function item(withProposal: boolean): InboxItem {
  return {
    finding,
    proposals: withProposal ? [proposal] : [],
    latest_proposal: withProposal ? proposal : null,
    stale: false,
  };
}

it("creates an exact-base proposal and human ACCEPT resolves the finding", async () => {
  let phase: "finding" | "proposal" | "accepted" = "finding";
  const calls: Array<{ method: string; path: string; body?: unknown }> = [];
  const accepted: DecisionResult = {
    decision: "ACCEPT",
    decision_id: "01JDECISION00000000000000",
    finding: { ...finding, status: "RESOLVED", resolved_at: "2026-08-26T10:02:00Z" },
    proposal: { ...proposal, status: "ACCEPTED" },
    accepted_revision_id: "01JNEWREVISION000000000000",
    approval_id: "01JAPPROVAL0000000000000",
  };

  const api: EditorialApi = async function api<T>(
    method: "GET" | "POST" | "PUT",
    path: string,
    body?: unknown,
  ): Promise<T> {
    calls.push({ method, path, body });
    if (method === "GET" && path.includes("/editorial/inbox")) {
      if (phase === "accepted") return [] as T;
      return [item(phase === "proposal")] as T;
    }
    if (method === "POST" && path.endsWith(`/findings/${finding.finding_id}/proposals`)) {
      phase = "proposal";
      return proposal as T;
    }
    if (method === "POST" && path.endsWith(`/${proposal.proposal_id}/accept`)) {
      phase = "accepted";
      return accepted as T;
    }
    throw new Error(`unexpected API call: ${method} ${path}`);
  };

  render(<EditorialPanel project={project} chapter={chapter} api={api} />);

  expect(await screen.findByText("This current passage needs one bounded editorial revision.")).toBeInTheDocument();
  expect(screen.getByText("CURRENT")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Editorial proposed text"), {
    target: { value: proposal.proposed_text },
  });
  fireEvent.change(screen.getByLabelText("Editorial proposal rationale"), {
    target: { value: proposal.rationale },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create exact-base proposal" }));

  expect(await screen.findByLabelText("Editorial proposal diff")).toHaveTextContent("+++ proposed");
  expect(screen.getByLabelText("Editorial proposal diff")).toHaveTextContent(
    "only becomes current after human acceptance",
  );

  fireEvent.change(screen.getByLabelText("Editorial decision reason"), {
    target: { value: "Owner approves this exact bounded edit" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Accept" }));

  const result = await screen.findByLabelText("Editorial decision result");
  expect(result).toHaveTextContent("ACCEPT · RESOLVED");
  expect(result).toHaveTextContent(accepted.accepted_revision_id ?? "");
  expect(await screen.findByText("No findings in this filter.")).toBeInTheDocument();

  expect(calls).toContainEqual({
    method: "POST",
    path: expect.stringContaining(`/findings/${finding.finding_id}/proposals`),
    body: {
      proposed_text: proposal.proposed_text,
      rationale: proposal.rationale,
      actor: "OWNER",
      actor_kind: "HUMAN",
    },
  });
  expect(calls).toContainEqual({
    method: "POST",
    path: expect.stringContaining(`/${proposal.proposal_id}/accept`),
    body: {
      actor: "OWNER",
      actor_kind: "HUMAN",
      reason: "Owner approves this exact bounded edit",
    },
  });
});
