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

export type ProviderLaneReadiness = {
  implementation_ready: boolean;
  live_promotion_required: boolean;
  credentials: Record<string, string>;
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

  return (
    <section className="panel">
      <h2>Provider Lane / Availability</h2>
      <p>
        Region: <strong>RU</strong> · WRITER production route:{" "}
        <strong>{writerReady ? "AVAILABLE" : "UNAVAILABLE"}</strong>
      </p>
      <p>
        Stage B:{" "}
        <strong>
          {readiness?.implementation_ready ? "IMPLEMENTATION READY" : "IMPLEMENTATION PENDING"}
        </strong>
        {" · "}
        <strong>
          {readiness?.live_promotion_required ? "LIVE PROMOTION REQUIRED" : "PROMOTION PENDING"}
        </strong>
        {" · "}
        <strong>
          {Object.values(readiness?.credentials ?? {}).some((state) => state === "AVAILABLE")
            ? "CREDENTIAL CHECK COMPLETE"
            : "CREDENTIAL NOT AVAILABLE"}
        </strong>
      </p>
      <p>Production routing requires verified regional policy and an explicit role promotion. A Russia-ready claim additionally requires Stage B live promotion acceptance.</p>
      {unavailableReason && <p className="error">Unavailable: {unavailableReason}</p>}
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
