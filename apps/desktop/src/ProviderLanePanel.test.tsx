import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import {
  ProviderLanePanel,
  type ProviderCapabilityView,
  type ProviderLaneReadiness,
} from "./ProviderLanePanel";

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

const readiness: ProviderLaneReadiness = {
  ready: false,
  routes_ready: false,
  production_ready: false,
  implementation_ready: true,
  live_promotion_required: true,
  credentials_ready: false,
  credentials: { yandex: "NOT AVAILABLE", gigachat: "NOT AVAILABLE" },
  required_launch_roles: ["WRITER", "EDITOR"],
  evaluation_role: {
    available: false,
    reason: "QUALITY_NOT_PROMOTED",
    provider: null,
    model: null,
  },
  roles: {
    WRITER: {
      available: false,
      reason: "QUALITY_NOT_PROMOTED",
      provider: null,
      model: null,
    },
    EDITOR: {
      available: false,
      reason: "QUALITY_NOT_PROMOTED",
      provider: null,
      model: null,
    },
    EVALUATOR: {
      available: false,
      reason: "QUALITY_NOT_PROMOTED",
      provider: null,
      model: null,
    },
  },
};

afterEach(cleanup);

it("shows fail-closed RU launch readiness without VPN guidance", () => {
  const { container } = render(
    <ProviderLanePanel
      capabilities={[yandex]}
      unavailableReason="QUALITY_NOT_PROMOTED"
      readiness={readiness}
    />,
  );

  expect(screen.getByText("Provider Lane / Availability")).toBeInTheDocument();
  expect(container).toHaveTextContent("Region: RU");
  expect(container).toHaveTextContent("launch routes (WRITER + EDITOR): UNAVAILABLE");
  expect(container).toHaveTextContent("WRITER route: UNAVAILABLE");
  expect(container).toHaveTextContent("EDITOR route: UNAVAILABLE");
  expect(container).toHaveTextContent("EVALUATOR evidence route: NOT PROMOTED");
  expect(container).toHaveTextContent("WRITER unavailable: QUALITY_NOT_PROMOTED");
  expect(container).toHaveTextContent("yandex / yandexgpt");
  expect(container).toHaveTextContent("generation: yes");
  expect(container).toHaveTextContent("embeddings: yes");
  expect(container).toHaveTextContent("promotion: CANDIDATE");
  expect(container).not.toHaveTextContent(/use vpn/i);
  expect(container).toHaveTextContent("Russia-ready claim additionally requires Stage B");
  expect(container).toHaveTextContent("IMPLEMENTATION READY");
  expect(container).toHaveTextContent("LIVE PROMOTION REQUIRED");
  expect(container).toHaveTextContent("CREDENTIAL CHECK REQUIRED");
});

it("does not treat WRITER-only availability as complete launch readiness", () => {
  const { container } = render(
    <ProviderLanePanel
      capabilities={[{ ...yandex, promotion: "PROMOTED", health: "HEALTHY" }]}
      unavailableReason={null}
      readiness={{
        ...readiness,
        roles: {
          ...readiness.roles,
          WRITER: {
            available: true,
            reason: null,
            provider: "yandex",
            model: "yandexgpt",
          },
        },
      }}
    />,
  );

  expect(container).toHaveTextContent("launch routes (WRITER + EDITOR): UNAVAILABLE");
  expect(container).toHaveTextContent("WRITER route: AVAILABLE");
  expect(container).toHaveTextContent("EDITOR route: UNAVAILABLE");
  expect(container).not.toHaveTextContent("PRODUCTION ROUTE READY");
});

it("shows production route ready only when runtime roles and credentials are ready", () => {
  const { container } = render(
    <ProviderLanePanel
      capabilities={[{ ...yandex, promotion: "PROMOTED", health: "HEALTHY" }]}
      unavailableReason={null}
      readiness={{
        ...readiness,
        ready: true,
        routes_ready: true,
        production_ready: true,
        live_promotion_required: false,
        credentials_ready: true,
        credentials: { yandex: "AVAILABLE", gigachat: "NOT AVAILABLE" },
        roles: {
          ...readiness.roles,
          WRITER: {
            available: true,
            reason: null,
            provider: "yandex",
            model: "yandexgpt",
          },
          EDITOR: {
            available: true,
            reason: null,
            provider: "yandex",
            model: "yandexgpt",
          },
        },
      }}
    />,
  );

  expect(container).toHaveTextContent("launch routes (WRITER + EDITOR): AVAILABLE");
  expect(container).toHaveTextContent("PRODUCTION ROUTE READY");
  expect(container).toHaveTextContent("CREDENTIALS READY");
});
