export type ProviderCapabilityView = {
  provider: string;
  model: string;
  config_id: string;
  region: string;
  roles: string[];
  generation: boolean;
  embeddings: boolean;
  structured_output: boolean;
  tools: boolean;
  legal: boolean;
  commercial: boolean;
  privacy_ok: boolean;
  promotion: string;
  health: string;
  matrix_version: string;
  verified_at: string;
};

export type ProviderRoleReadiness = {
  available: boolean;
  reason: string | null;
  provider: string | null;
  model: string | null;
};

export type ProviderLaneReadiness = {
  ready: boolean;
  routes_ready: boolean;
  production_ready: boolean;
  implementation_ready: boolean;
  live_promotion_required: boolean;
  credentials_ready: boolean;
  credentials: Record<string, string>;
  required_launch_roles: string[];
  evaluation_role: ProviderRoleReadiness;
  roles: Record<string, ProviderRoleReadiness>;
};

export function ProviderLanePanel({
  capabilities,
  unavailableReason,
  readiness,
}: {
  capabilities: ProviderCapabilityView[];
  unavailableReason: string | null;
  readiness: ProviderLaneReadiness | null;
}) {
  const writerReady = unavailableReason === null;
  const routesReady = readiness?.routes_ready ?? false;
  const productionReady = readiness?.production_ready ?? false;

  return (
    <section className="panel">
      <h2>Provider Lane / Availability</h2>
      <p>
        Region: <strong>RU</strong> · launch routes ({readiness?.required_launch_roles.join(" + ") ?? "WRITER + EDITOR"}):{" "}
        <strong>{routesReady ? "AVAILABLE" : "UNAVAILABLE"}</strong>
      </p>
      <p>
        WRITER route: <strong>{writerReady ? "AVAILABLE" : "UNAVAILABLE"}</strong>
        {readiness?.roles.EDITOR && (
          <>
            {" · "}EDITOR route:{" "}
            <strong>{readiness.roles.EDITOR.available ? "AVAILABLE" : "UNAVAILABLE"}</strong>
          </>
        )}
        {readiness?.evaluation_role && (
          <>
            {" · "}EVALUATOR evidence route:{" "}
            <strong>{readiness.evaluation_role.available ? "AVAILABLE" : "NOT PROMOTED"}</strong>
          </>
        )}
      </p>
      <p>
        Stage B:{" "}
        <strong>
          {readiness?.implementation_ready ? "IMPLEMENTATION READY" : "IMPLEMENTATION PENDING"}
        </strong>
        {" · "}
        <strong>
          {productionReady
            ? "PRODUCTION ROUTE READY"
            : readiness?.live_promotion_required
              ? "LIVE PROMOTION REQUIRED"
              : "LIVE EVIDENCE / CREDENTIAL GATE"}
        </strong>
        {" · "}
        <strong>{readiness?.credentials_ready ? "CREDENTIALS READY" : "CREDENTIAL CHECK REQUIRED"}</strong>
      </p>
      <p>
        Production routing requires verified regional policy, current LIVE health and explicit
        role promotion for WRITER and EDITOR. EVALUATOR is an evidence role and does not by itself
        make the user runtime unavailable. A Russia-ready claim additionally requires Stage B live
        promotion acceptance.
      </p>
      {unavailableReason && <p className="error">WRITER unavailable: {unavailableReason}</p>}
      <ul>
        {capabilities.map((item) => (
          <li key={`${item.provider}:${item.model}:${item.config_id}`}>
            <strong>
              {item.provider} / {item.model}
            </strong>{" "}
            — {item.region}; roles: {item.roles.join(", ") || "none"}; generation:{" "}
            {item.generation ? "yes" : "no"}; embeddings: {item.embeddings ? "yes" : "no"};
            structured output: {item.structured_output ? "yes" : "no"}; legal:{" "}
            {item.legal ? "verified" : "blocked/unknown"}; commercial:{" "}
            {item.commercial ? "verified" : "blocked/unknown"}; privacy:{" "}
            {item.privacy_ok ? "verified" : "blocked/unknown"}; promotion: {item.promotion}; health:{" "}
            {item.health}; verified: {item.verified_at}
          </li>
        ))}
      </ul>
    </section>
  );
}
