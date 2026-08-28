import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ProviderLanePanel, type ProviderCapabilityView } from "./ProviderLanePanel";

const yandex: ProviderCapabilityView = {
  provider: "yandex",
  model: "yandexgpt",
  config_id: "latest-discovery",
  region: "RU",
  roles: ["WRITER", "EDITOR", "EVALUATOR"],
  generation: true,
  embeddings: true,
  structured_output: true,
  tools: false,
  legal: true,
  commercial: true,
  privacy_ok: true,
  promotion: "CANDIDATE",
  health: "UNKNOWN",
  matrix_version: "m8-2026-08-27",
  verified_at: "2026-08-27",
};

afterEach(cleanup);

it("shows fail-closed RU provider readiness without VPN guidance", () => {
  const { container } = render(
    <ProviderLanePanel capabilities={[yandex]} unavailableReason="QUALITY_NOT_PROMOTED" />,
  );

  expect(screen.getByText("Provider Lane / Availability")).toBeInTheDocument();
  expect(container).toHaveTextContent("Region: RU");
  expect(container).toHaveTextContent("Russia-ready (WRITER): NO");
  expect(container).toHaveTextContent("Unavailable: QUALITY_NOT_PROMOTED");
  expect(container).toHaveTextContent("yandex / yandexgpt");
  expect(container).toHaveTextContent("generation: yes");
  expect(container).toHaveTextContent("embeddings: yes");
  expect(container).toHaveTextContent("promotion: CANDIDATE");
  expect(container).not.toHaveTextContent(/use vpn/i);
});

it("shows a ready writer lane only when routing has no unavailable reason", () => {
  const { container } = render(
    <ProviderLanePanel
      capabilities={[{ ...yandex, promotion: "PROMOTED", health: "HEALTHY" }]}
      unavailableReason={null}
    />,
  );

  expect(container).toHaveTextContent("Russia-ready (WRITER): YES");
  expect(container).not.toHaveTextContent("Unavailable:");
});
