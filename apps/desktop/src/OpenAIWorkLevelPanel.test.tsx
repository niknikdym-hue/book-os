import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it } from "vitest";
import { OpenAIWorkLevelPanel } from "./OpenAIWorkLevelPanel";
import {
  clearPendingOpenAIWorkLevel,
  getPendingOpenAIWorkLevel,
} from "./openaiWorkLevel";

beforeEach(() => {
  clearPendingOpenAIWorkLevel();
});

it("exposes exactly Medium, High and Extra High for the next OpenAI operation", () => {
  render(<OpenAIWorkLevelPanel />);

  expect(screen.getByLabelText("Модель Astra")).toHaveValue("gpt-6-astra");
  expect(screen.getByRole("option", { name: "GPT-6 Astra" })).toBeInTheDocument();

  expect(screen.getByRole("button", { name: "Medium" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "High" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Extra High" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Extra High" }));
  expect(getPendingOpenAIWorkLevel()).toBe("xhigh");
  expect(screen.getByText("Extra High", { selector: "span" })).toBeInTheDocument();
});
