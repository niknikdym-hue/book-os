export type EditorialApi = <T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
) => Promise<T>;

export type EditorialRole =
  | "DEVELOPMENTAL_EDITOR"
  | "CROSS_BOOK_AUDITOR"
  | "FACT_CHECKER"
  | "LITERARY_EDITOR"
  | "STYLE_GUARDIAN";

export type FindingStatus = "OPEN" | "RESOLVED" | "WAIVED" | "SUPERSEDED";
export type FindingSeverity = "INFO" | "MINOR" | "MAJOR" | "CRITICAL";

export type FindingView = {
  finding_id: string;
  run_id: string | null;
  book_id: string;
  role: EditorialRole | string;
  category: string;
  target_kind: string;
  target_entity_id: string;
  chapter_id: string | null;
  unit_id: string | null;
  base_revision_id: string;
  base_revision_hash: string;
  diagnosis: string;
  why: string;
  evidence: Record<string, unknown>;
  severity: FindingSeverity | string;
  confidence: number;
  expected_effect: string;
  risks: string;
  actor: string;
  actor_kind: string;
  status: FindingStatus | string;
  created_at: string;
  resolved_at: string | null;
};

export type ProposalView = {
  proposal_id: string;
  finding_id: string;
  status: string;
  stale: boolean;
  base_revision_id: string;
  base_revision_hash: string;
  proposed_content_hash: string;
  rationale: string;
  proposed_text: string;
  diff: string;
  created_at: string;
};

export type InboxItem = {
  finding: FindingView;
  proposals: ProposalView[];
  latest_proposal: ProposalView | null;
  stale: boolean;
};

export type EditorialRunResult = {
  run_id: string;
  role: EditorialRole | string;
  findings: FindingView[];
};

export type DecisionResult = {
  decision: "ACCEPT" | "REJECT" | "REQUEST_REVISION" | "WAIVE" | string;
  decision_id: string;
  finding: FindingView;
  proposal: ProposalView | null;
  accepted_revision_id: string | null;
  approval_id: string | null;
};
