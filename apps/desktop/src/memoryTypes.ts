export type MemoryApi = <T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
) => Promise<T>;

export type MemorySearchMode = "LEXICAL" | "SEMANTIC" | "HYBRID";
export type MemoryScope = "CURRENT" | "HISTORY";
export type MemoryObjectKind =
  | "MANUSCRIPT_UNIT"
  | "BOOK_CONTRACT"
  | "CHAPTER_CONTRACT"
  | "CLAIM";

export type MemoryIndexStatus = {
  book_id: string;
  status: "EMPTY" | "LEXICAL_READY" | "SEMANTIC_READY" | "FAILED" | string;
  document_count: number;
  embedding_count: number;
  provider: string | null;
  model: string | null;
  model_version: string | null;
  config_hash: string | null;
  dimension: number | null;
  updated_at: string | null;
};

export type MemorySearchResult = {
  memory_id: string;
  object_kind: string;
  object_id: string;
  chapter_id: string | null;
  revision_id: string;
  revision_hash: string;
  content_hash: string;
  source_status: string;
  currentness: "CURRENT" | "HISTORY" | string;
  text: string;
  lexical_score: number | null;
  semantic_score: number | null;
  fused_score: number | null;
  lexical_rank: number | null;
  semantic_rank: number | null;
  fused_rank: number | null;
};
