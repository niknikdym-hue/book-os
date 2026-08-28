export type ProviderCapabilityView = { provider: string; model: string; region: string; promotion: string; health: string; commercial: boolean };

export function ProviderLanePanel({ capabilities, unavailableReason }: { capabilities: ProviderCapabilityView[]; unavailableReason: string | null }) {
  return <section className="panel"><h2>Provider Lane / Availability</h2><p>Russia/no-VPN route policy. Provider access requires role promotion.</p>{unavailableReason && <p className="error">Unavailable: {unavailableReason}</p>}<ul>{capabilities.map((item) => <li key={`${item.provider}:${item.model}`}>{item.provider} / {item.model} — {item.region}, {item.promotion}, {item.health}{!item.commercial && " (commercial route unavailable)"}</li>)}</ul></section>;
}
