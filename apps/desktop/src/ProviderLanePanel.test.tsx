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

const readiness = {
  implementation_ready: true,
  live_promotion_required: true,
  credentials: { yandex: "NOT AVAILABLE", gigachat: "NOT AVAILABLE" },
};

afterEach(cleanup);

it("shows fail-closed RU provider readiness without VPN guidance", () => {
  const { container } = render(
    <ProviderLanePanel
      capabilities={[yandex]}
      unavailableReason="QUALITY_NOT_PROMOTED"
      readiness={readiness}
    />,
  );

  expect(screen.getByText("Provider Lane / Availability")).toBeInTheDocument();
  expect(container).toHaveTextContent("Region: RU");
  expect(container).toHaveTextContent("WRITER production route: UNAVAILABLE");
  expect(container).toHaveTextContent("Unavailable: QUALITY_NOT_PROMOTED");
  expect(container).toHaveTextContent("yandex / yandexgpt");
  expect(container).toHaveTextContent("generation: yes");
  expect(container).toHaveTextContent("embeddings: yes");
  expect(container).toHaveTextContent("promotion: CANDIDATE");
  expect(container).not.toHaveTextContent(/use vpn/i);
  expect(container).toHaveTextContent("Russia-ready claim additionally requires Stage B");
  expect(container).toHaveTextContent("IMPLEMENTATION READY");
  expect(container).toHaveTextContent("LIVE PROMOTION REQUIRED");
  expect(container).toHaveTextContent("CREDENTIAL NOT AVAILABLE");
});

it("shows a ready writer lane only when routing has no unavailable reason", () => {
  const { container } = render(
    <ProviderLanePanel
      capabilities={[{ ...yandex, promotion: "PROMOTED", health: "HEALTHY" }]}
      unavailableReason={null}
      readiness={readiness}
    />,
  );

  expect(container).toHaveTextContent("WRITER production route: AVAILABLE");
  expect(container).not.toHaveTextContent("Unavailable:");
});
