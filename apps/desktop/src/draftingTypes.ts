import type { ChapterView, ProjectView } from "./types";

export type DraftRunView = {
  task_id: string;
  run_id: string;
  task_status: string;
  run_status: string;
  provider: string;
  model: string;
  prompt_id: string;
  prompt_version: string;
  prompt_hash: string;
  input_revision_id: string;
  input_revision_hash: string;
  unit_id: string | null;
  revision_id: string | null;
  revision_status: string | null;
  text: string | null;
  notes: string[];
  provider_run_id: string | null;
  usage: Record<string, unknown>;
  error_code: string | null;
  error_message: string | null;
};

export type DraftApi = <T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
) => Promise<T>;

export type DraftingPanelProps = {
  project: ProjectView;
  chapter: ChapterView | null;
  api?: DraftApi;
};
