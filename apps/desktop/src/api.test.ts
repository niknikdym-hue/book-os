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

it("defaults an Astra execution to High when no operation-specific mode was selected", async () => {
  await coreApi("POST", "/api/projects/book/planning/architecture", {
    provider: "openai",
    model: "gpt-6-astra",
    max_cost_usd: 1,
  });

  expect(invokeMock).toHaveBeenCalledWith("core_api", {
    request: {
      method: "POST",
      path: "/api/projects/book/planning/architecture",
      body: {
        provider: "openai",
        model: "gpt-6-astra",
        max_cost_usd: 1,
        reasoning_effort: "high",
      },
    },
  });
});

it("maps Extra High to xhigh, consumes it after one Astra attempt, then returns to High", async () => {
  setPendingOpenAIWorkLevel("xhigh");

  await coreApi("POST", "/api/projects/book/chapters/chapter/drafts", {
    provider: "openai",
    model: "gpt-6-astra",
    max_cost_usd: 1,
  });

  expect(invokeMock).toHaveBeenLastCalledWith("core_api", {
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

  await coreApi("POST", "/api/projects/book/planning/book-contract", {
    provider: "openai",
    model: "gpt-6-astra",
    max_cost_usd: 1,
  });
  expect(invokeMock).toHaveBeenLastCalledWith("core_api", {
    request: {
      method: "POST",
      path: "/api/projects/book/planning/book-contract",
      body: {
        provider: "openai",
        model: "gpt-6-astra",
        max_cost_usd: 1,
        reasoning_effort: "high",
      },
    },
  });
});

it("preserves an explicit Astra effort even if a pending value exists", async () => {
  setPendingOpenAIWorkLevel("medium");

  await coreApi("POST", "/api/projects/book/chapters/chapter/drafts", {
    provider: "openai",
    model: "gpt-6-astra",
    max_cost_usd: 1,
    reasoning_effort: "xhigh",
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
});

it("does not attach an Astra reasoning level to GPT-5.6 Sol", async () => {
  await coreApi("POST", "/api/projects/book/chapters/chapter/drafts", {
    provider: "openai",
    model: "gpt-5.6-sol",
    max_cost_usd: 1,
  });

  expect(invokeMock).toHaveBeenCalledWith("core_api", {
    request: {
      method: "POST",
      path: "/api/projects/book/chapters/chapter/drafts",
      body: {
        provider: "openai",
        model: "gpt-5.6-sol",
        max_cost_usd: 1,
      },
    },
  });
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
