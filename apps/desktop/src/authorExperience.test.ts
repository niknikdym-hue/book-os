import { expect, it } from "vitest";
import { bookProgress, bookStageStates, currentBookStage, money } from "./authorExperience";
import type { ProjectView } from "./types";

function view(workflowStage: string, contract = "APPROVED", architecture = "APPROVED"): ProjectView {
  return {
    book_id: "01JBOOK000000000000000000",
    working_title: "Книга",
    mode: "BOOK_FROM_ZERO",
    domain: "BUSINESS_NONFICTION",
    primary_subtype: "Strategy",
    secondary_subtype: null,
    profile_version: "business-nonfiction-v0.1",
    workflow_stage: workflowStage,
    book_contract: contract
      ? { entity_id: "c", revision_id: "cr", status: contract, authority_revision_id: "cr", authority_status: contract, content: {} }
      : null,
    architecture: architecture
      ? { entity_id: "a", revision_id: "ar", status: architecture, authority_revision_id: "ar", authority_status: architecture, content: {} }
      : null,
    chapters: architecture
      ? [{
          chapter_id: "chapter",
          ordinal: 1,
          working_title: "Глава",
          architecture_role: "Роль",
          workflow_state: "CONTRACT_APPROVED",
          chapter_contract: {
            entity_id: "cc",
            revision_id: "ccr",
            status: "APPROVED",
            authority_revision_id: "ccr",
            authority_status: "APPROVED",
            content: {},
          },
        }]
      : [],
  };
}

it("does not let the frontend unlock stages ahead of backend authority", () => {
  const project = view("BOOK DEFINITION", "", "");
  const states = bookStageStates(project, null);
  expect(states.intent).toBe("current");
  expect(states.plan).toBe("locked");
  expect(states.architecture).toBe("locked");
  expect(states.release).toBe("locked");
});

it("maps internal workflow stages onto the seven author stages", () => {
  const project = view("WHOLE-BOOK EDIT");
  const states = bookStageStates(project, null);
  expect(states.intent).toBe("done");
  expect(states.plan).toBe("done");
  expect(states.architecture).toBe("done");
  expect(states.writing).toBe("done");
  expect(states.editing).toBe("current");
  expect(currentBookStage(project, null)).toBe("editing");
});

it("uses durable runtime progress and keeps money labels exact", () => {
  const project = view("WRITING");
  expect(bookProgress(project, {
    run_id: "run",
    status: "RUNNING",
    phase: "CHAPTER_DRAFT",
    progress_completed: 7,
    progress_total: 20,
  })).toBe(35);
  expect(money(4.2)).toBe("$4.20");
});
