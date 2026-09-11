import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it } from "vitest";
import { OpenAIWorkLevelPanel } from "./OpenAIWorkLevelPanel";

type Call = { method: string; path: string; body?: unknown };

it("keeps API-key administration in collapsed Advanced settings", async () => {
  const calls: Call[] = [];
  let configured = false;
  const api = async function api<T>(
    method: "GET" | "POST" | "PUT",
    path: string,
    body?: unknown,
  ): Promise<T> {
    calls.push({ method, path, body });
    if (method === "GET" && path === "/api/launch/readiness") {
      return {
        openai_credential_state: configured ? "AVAILABLE" : "NOT_AVAILABLE",
      } as T;
    }
    if (method === "POST" && path === "/api/launch/openai-key") {
      configured = true;
      return {} as T;
    }
    throw new Error(`unexpected request: ${method} ${path}`);
  };

  render(<OpenAIWorkLevelPanel api={api} />);

  const settings = await screen.findByText("Настройки / Advanced");
  expect(settings.closest("details")).not.toHaveAttribute("open");
  expect(screen.queryByRole("button", { name: "Medium" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "High" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Extra High" })).not.toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("API-ключ OpenAI"), {
    target: { value: "sk-test-key-12345" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Сохранить OpenAI в Keychain" }));

  await waitFor(() =>
    expect(calls).toContainEqual({
      method: "POST",
      path: "/api/launch/openai-key",
      body: { api_key: "sk-test-key-12345" },
    }),
  );
  expect(await screen.findByText(/OpenAI подключён/)).toBeInTheDocument();
});
