import { beforeEach, expect, it, vi } from "vitest";

const { invokeMock } = vi.hoisted(() => ({ invokeMock: vi.fn() }));

vi.mock("@tauri-apps/api/core", () => ({ invoke: invokeMock }));

import { coreApi } from "./api";
import {
  clearPendingOpenAIWorkLevel,
  setPendingOpenAIWorkLevel,
} from "./openaiWorkLevel";

beforeEach(() => {
  invokeMock.mockReset();
  invokeMock.mockResolvedValue({ ok: true });
  clearPendingOpenAIWorkLevel();
});

it("requires an explicit work level for an OpenAI execution", async () => {
  await expect(
    coreApi("POST", "/api/projects/book/planning/architecture", {
      provider: "openai",
      model: "gpt-6-astra",
      max_cost_usd: 1,
    }),
  ).rejects.toThrow(/Medium, High или Extra High/);
  expect(invokeMock).not.toHaveBeenCalled();
});

it("maps Extra High to xhigh and consumes it after one OpenAI attempt", async () => {
  setPendingOpenAIWorkLevel("xhigh");

  await coreApi("POST", "/api/projects/book/chapters/chapter/drafts", {
    provider: "openai",
    model: "gpt-6-astra",
    max_cost_usd: 1,
  });

  expect(invokeMock).toHaveBeenCalledWith("core_api", {
    request: {
      method: "POST",
      path: "/api/projects/book/chapters/chapter/drafts",
      body: {
        provider: "openai",
        model: "gpt-6-astra",
        max_cost_usd: 1,
        reasoning_effort: "xhigh",
      },
    },
  });

  await expect(
    coreApi("POST", "/api/projects/book/planning/book-contract", {
      provider: "openai",
      model: "gpt-6-astra",
      max_cost_usd: 1,
    }),
  ).rejects.toThrow(/выберите уровень работы OpenAI/i);
});

it("does not impose the OpenAI work-level contract on another provider", async () => {
  await coreApi("POST", "/api/projects/book/planning/book-contract", {
    provider: "yandex",
    model: "aliceai-llm",
    max_cost_usd: 1,
  });

  expect(invokeMock).toHaveBeenCalledWith("core_api", {
    request: {
      method: "POST",
      path: "/api/projects/book/planning/book-contract",
      body: {
        provider: "yandex",
        model: "aliceai-llm",
        max_cost_usd: 1,
      },
    },
  });
});
