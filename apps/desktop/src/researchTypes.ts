export type ResearchApi = <T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
) => Promise<T>;

export type ClaimView = {
  claim_id: string;
  book_id: string;
  chapter_id: string;
  unit_id: string;
  manuscript_revision_id: string;
  manuscript_revision_hash: string;
  normalized_text: string;
  claim_type: string;
  materiality: string;
  required_evidence_level: string;
  verification_state: string;
  evidence_count: number;
  created_at: string;
  updated_at: string;
};

export type ResearchCandidate = {
  provider: string;
  external_id: string;
  title: string;
  authors: string[];
  organization: string | null;
  publication_date: string | null;
  publication_year: number | null;
  doi: string | null;
  canonical_url: string | null;
  container_title: string | null;
  source_type: string;
  abstract: string | null;
  citation_count: number | null;
  provider_url: string | null;
  raw_identifiers: Record<string, string>;
};

export type SourceView = {
  source_id: string;
  canonical_key: string;
  source_type: string;
  title: string;
  authors: string[];
  organization: string | null;
  publication_date: string | null;
  publication_year: number | null;
  doi: string | null;
  canonical_url: string | null;
  container_title: string | null;
  abstract: string | null;
  citation_count: number | null;
  primary_secondary: string;
  access_status: "METADATA_ONLY" | "ABSTRACT_AVAILABLE" | "FULL_SOURCE_INSPECTED";
  identifiers: Record<string, string[]>;
};

export type EvidenceView = {
  evidence_id: string;
  claim_id: string;
  source_id: string;
  relationship: "SUPPORTS" | "PARTIALLY_SUPPORTS" | "CONTRADICTS" | "CONTEXT_ONLY";
  pointer: string;
  note: string;
  strength: "WEAK" | "MODERATE" | "STRONG";
  limitations: string;
  actor: string;
  status: "ACTIVE" | "SUPERSEDED";
  supersedes_evidence_id: string | null;
  created_at: string;
};

export type CitationCheckView = {
  identifier: string;
  resolved: boolean;
  source_id: string | null;
  evidence_id: string | null;
  reason: string;
};
