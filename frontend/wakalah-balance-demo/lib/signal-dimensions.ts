export type TrustDimension = "hijack" | "identity" | "continuity" | "context" | "binding";

export const DIMENSION_ORDER: TrustDimension[] = [
  "hijack",
  "identity",
  "continuity",
  "context",
  "binding",
];

export const DIMENSION_LABELS: Record<TrustDimension, string> = {
  hijack: "Hijack",
  identity: "Identity",
  continuity: "Continuity",
  context: "Context",
  binding: "Binding",
};

// Live `nac.call` events don't carry `dimension` themselves (only the final
// decision's evidenceSummary does), so this is the fallback used to group
// cards while a run is still streaming. Adjust if your backend's actual
// per-signal dimensions differ from this mapping.
const SIGNAL_DIMENSION: Record<string, TrustDimension> = {
  sim_swap: "hijack",
  device_swap: "hijack",
  call_forwarding: "hijack",
  kyc_match: "identity",
  number_recycling: "continuity",
  tenure: "continuity",
  reachability: "context",
  location_verification: "context",
  number_verification: "binding",
};

export function dimensionForSignal(signal: string): TrustDimension {
  return SIGNAL_DIMENSION[signal] ?? "context";
}