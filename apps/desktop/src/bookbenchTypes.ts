export type Finding = {
  finding_id: string;
  dimension: string;
  category: string;
  location: string;
  evidence: Record<string, unknown>;
  severity: "INFO" | "ATTENTION" | "BLOCKING";
  confidence: number;
  recommended_action: string;
};

export type Dimension = {
  dimension: string;
  state: "PASS" | "ATTENTION" | "BLOCKING";
  findings: Finding[];
  run_ids: string[];
  metrics: Record<string, unknown>;
};

export type Report = {
  snapshot_id: string;
  snapshot_hash: string;
  current: boolean;
  dimensions: Dimension[];
  blocking_dimensions: string[];
};

export type Snapshot = {
  snapshot_id: string;
  snapshot_hash: string;
  current: boolean;
  scope: "BOOK" | "CHAPTER" | "MANUSCRIPT_UNIT";
  chapter_id: string | null;
  unit_id: string | null;
};

export type EvaluationRun = {
  evaluation_id: string;
  independence_state: "INDEPENDENT" | "SAME_CONFIG" | "UNKNOWN";
  latency_ms: number;
  cost_usd: number | null;
  output: Record<string, unknown>;
};

export type PairwiseResult = {
  evaluation_id: string;
  seed: number;
  labels: Record<"A" | "B", string>;
  winner_candidate_id: string | null;
  output: Record<string, unknown>;
};

export type SemanticResult = {
  evaluation_ids: string[];
  embedding_config: Record<string, unknown>;
  config_hash: string;
};

export type VoiceFingerprint = {
  fingerprint_id: string;
  name: string;
  extractor_version: string;
  fingerprint_hash: string;
  reference_snapshot_id: string;
  reference_revisions: Array<{ revision_id: string; revision_hash: string }>;
  features: Record<string, unknown>;
};

export type VoiceComparison = {
  fingerprint_id: string;
  target_snapshot_id: string;
  feature_deltas: Record<string, number>;
  target_features: Record<string, unknown>;
  diagnostic_only: boolean;
};

export type DatasetSnapshot = {
  dataset_snapshot_id: string;
  name: string;
  version: number;
  dataset_hash: string;
  case_count: number;
};

export type Scorecard = {
  scorecard_id: string;
  dataset_snapshot_id: string;
  config_id: string;
  config_hash: string;
  role: string;
  dimensions: Record<string, Record<string, unknown>>;
  severe_failure_count: number;
  pass_count: number;
  attention_count: number;
  blocking_count: number;
  latency_ms: number;
  cost_usd: number;
  usage: Record<string, unknown>;
};
