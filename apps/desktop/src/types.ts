export type CoreHealth = { status: string; version: string };

export type DocumentView = {
  entity_id: string;
  revision_id: string;
  status: string;
  authority_revision_id: string;
  authority_status: string;
  content: Record<string, unknown>;
};

export type ChapterView = {
  chapter_id: string;
  ordinal: number;
  working_title: string;
  architecture_role: string;
  workflow_state: string;
  chapter_contract: DocumentView | null;
};

export type ProjectSummary = {
  book_id: string;
  working_title: string;
  primary_subtype: string;
  secondary_subtype: string | null;
  workflow_stage: string;
};

export type ProjectView = ProjectSummary & {
  mode: string;
  domain: string;
  profile_version: string;
  book_contract: DocumentView | null;
  architecture: DocumentView | null;
  chapters: ChapterView[];
};

export type BookContractPayload = {
  reader: string;
  reader_problem: string;
  central_promise: string;
  central_thesis: string;
  unique_angle: string;
  reader_trajectory: string;
  explicit_exclusions: string[];
  evidence_policy: string;
  voice_genre_constraints: string;
  readiness_criteria: string[];
};

export type ArchitectureChapter = {
  chapter_id?: string | null;
  title: string;
  purpose: string;
  new_contribution: string;
  dependencies: string[];
  transition: string;
};

export type BookArchitecturePayload = {
  parts: Array<{
    title: string;
    purpose: string;
    chapters: ArchitectureChapter[];
  }>;
  intellectual_progression: string;
  concept_allocation: string;
  promise_thesis_coverage: string;
  major_transitions: string;
};

export type ChapterContractPayload = {
  chapter_purpose: string;
  new_contribution: string;
  reader_prior_state: string;
  reader_after_state: string;
  required_claims: string[];
  required_or_permitted_research: string[];
  required_scenes_examples: string[];
  reserved_elsewhere: string[];
  opening_requirements: string;
  ending_requirements: string;
  transition_requirements: string;
};
