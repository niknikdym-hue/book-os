import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
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

it("shows fail-closed RU provider readiness without VPN guidance", () => {
  render(
    <ProviderLanePanel capabilities={[yandex]} unavailableReason="QUALITY_NOT_PROMOTED" />,
  );

  expect(screen.getByText("Provider Lane / Availability")).toBeInTheDocument();
  expect(screen.getByText(/Region: RU/)).toBeInTheDocument();
  expect(screen.getByText(/Russia-ready \(WRITER\): NO/)).toBeInTheDocument();
  expect(screen.getByText(/Unavailable: QUALITY_NOT_PROMOTED/)).toBeInTheDocument();
  expect(screen.getByText(/yandex \/ yandexgpt/)).toBeInTheDocument();
  expect(screen.getByText(/generation: yes/)).toBeInTheDocument();
  expect(screen.getByText(/embeddings: yes/)).toBeInTheDocument();
  expect(screen.getByText(/promotion: CANDIDATE/)).toBeInTheDocument();
  expect(screen.queryByText(/use vpn/i)).not.toBeInTheDocument();
});

it("shows a ready writer lane only when routing has no unavailable reason", () => {
  render(
    <ProviderLanePanel
      capabilities={[{ ...yandex, promotion: "PROMOTED", health: "HEALTHY" }]}
      unavailableReason={null}
    />,
  );

  expect(screen.getByText(/Russia-ready \(WRITER\): YES/)).toBeInTheDocument();
  expect(screen.queryByText(/Unavailable:/)).not.toBeInTheDocument();
});
