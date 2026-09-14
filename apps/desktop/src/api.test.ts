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

it("requires a separate human confirmation for every exact AudioScript ATTENTION finding", async () => {
  const script = {
    audio_script_id: "audio-1",
    status: "PROPOSED",
    quality_checks: [
      {
        findings: [
          {
            code: "TERM_REVIEW",
            location: "chapter-1:p2",
            detail: "Проверьте произношение CRM.",
            severity: "ATTENTION",
          },
          {
            code: "TERM_REVIEW",
            location: "chapter-4:p7",
            detail: "Проверьте ударение в слове замок.",
            severity: "ATTENTION",
          },
        ],
      },
    ],
  };
  const confirmMock = vi.spyOn(window, "confirm").mockReturnValue(true);
  invokeMock.mockImplementation(async (command: string, args?: unknown) => {
    if (command === "core_health") return { ok: true };
    const request = (args as {
      request: { method: string; path: string; body: unknown };
    }).request;
    if (
      request.method === "GET" &&
      request.path === "/api/projects/book/auto-book/audio-script"
    ) {
      return script;
    }
    return { ok: true };
  });

  await coreApi("POST", "/api/projects/book/auto-book/audio-script/approve", {
    human_actor: "Елена Дым",
    accepted_attention_codes: ["TERM_REVIEW"],
  });

  expect(confirmMock).toHaveBeenCalledTimes(2);
  expect(confirmMock.mock.calls[0][0]).toContain("chapter-1:p2");
  expect(confirmMock.mock.calls[1][0]).toContain("chapter-4:p7");
  const approvalCall = invokeMock.mock.calls.find((call) => {
    if (call[0] !== "core_api") return false;
    const request = (call[1] as {
      request: { method: string; path: string };
    }).request;
    return (
      request.method === "POST" &&
      request.path === "/api/projects/book/auto-book/audio-script/approve"
    );
  });
  expect(approvalCall).toBeTruthy();
  expect(
    (approvalCall?.[1] as {
      request: { body: { accepted_attention_codes: string[] } };
    }).request.body.accepted_attention_codes,
  ).toEqual([
    "TERM_REVIEW␟chapter-1:p2␟Проверьте произношение CRM.",
    "TERM_REVIEW␟chapter-4:p7␟Проверьте ударение в слове замок.",
  ]);
  confirmMock.mockRestore();
});

it("does not send audio approval when one exact ATTENTION finding is not confirmed", async () => {
  const confirmMock = vi
    .spyOn(window, "confirm")
    .mockReturnValueOnce(true)
    .mockReturnValueOnce(false);
  invokeMock.mockImplementation(async (command: string, args?: unknown) => {
    if (command === "core_health") return { ok: true };
    const request = (args as {
      request: { method: string; path: string; body: unknown };
    }).request;
    if (
      request.method === "GET" &&
      request.path === "/api/projects/book/auto-book/audio-script"
    ) {
      return {
        audio_script_id: "audio-1",
        status: "PROPOSED",
        quality_checks: [
          {
            findings: [
              {
                code: "AUDIO_REVIEW",
                location: "chapter-1:p1",
                detail: "Первое замечание.",
                severity: "ATTENTION",
              },
              {
                code: "AUDIO_REVIEW",
                location: "chapter-2:p3",
                detail: "Второе замечание.",
                severity: "ATTENTION",
              },
            ],
          },
        ],
      };
    }
    return { ok: true };
  });

  await expect(
    coreApi("POST", "/api/projects/book/auto-book/audio-script/approve", {
      human_actor: "Елена Дым",
      accepted_attention_codes: [],
    }),
  ).rejects.toThrow("не подтверждено замечание AUDIO_REVIEW @ chapter-2:p3");

  const approvalCalls = invokeMock.mock.calls.filter((call) => {
    if (call[0] !== "core_api") return false;
    const request = (call[1] as {
      request: { method: string; path: string };
    }).request;
    return (
      request.method === "POST" &&
      request.path === "/api/projects/book/auto-book/audio-script/approve"
    );
  });
  expect(approvalCalls).toHaveLength(0);
  confirmMock.mockRestore();
});
