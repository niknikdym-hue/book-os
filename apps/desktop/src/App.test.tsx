import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { App } from "./App";
vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn().mockResolvedValue({ status: "healthy", version: "0.1.0" }) }));
it("shows authenticated Local Core health", async () => { render(<App />); expect(await screen.findByText("Local Core healthy")).toBeInTheDocument(); });
