"use client";

import type { EvaluateResponse } from "@/lib/types";

const decisionStyles = {
  allow: { wrapper: "border-emerald-300 bg-emerald-50", text: "text-emerald-700", icon: "✅" },
  challenge: { wrapper: "border-amber-300 bg-amber-50", text: "text-amber-700", icon: "🟡" },
  deny: { wrapper: "border-red-300 bg-red-50", text: "text-red-700", icon: "⛔" },
} as const;

const REASON_SENTENCES: Record<string, string> = {
  MANDATE_NOT_ACTIVE: "Mandate revoked or expired",
  AMOUNT_EXCEEDS_MANDATE_LIMIT: "Above what the principal authorized",
  BENEFICIARY_NOT_PERMITTED: "Outside the mandate's beneficiary list",
  IDENTITY_MISMATCH: "Claimed identity fails against operator records",
  NUMBER_RECYCLED: "The subscriber behind this number changed",
  SIM_SWAP_RECENT_HIGH_VALUE: "SIM swapped recently, on a high-value transfer",
  NEW_BENEFICIARY_MATERIAL_VALUE: "First-ever payment to this beneficiary at material size",
  SIM_SWAP_RECENT_LOW_VALUE: "Recent SIM swap, smaller amount",
  DEVICE_SWAP_RECENT: "Same SIM in a new device recently",
  CALL_FORWARDING_ACTIVE: "Calls are being silently forwarded",
  PRINCIPAL_CHALLENGE_ONLY: "Principal under challenge-only after a hijack signal",
  NUMBER_NOT_VERIFIED: "Phone ownership could not be verified",
  DEVICE_UNREACHABLE: "Device is currently unreachable",
  LOCATION_INCONSISTENT: "Device outside the expected area",
  INSUFFICIENT_EVIDENCE: "Required checks could not be completed",
  AGENT_REQUESTED_STEP_UP: "The agent asked for additional verification",
};

function humanize(code: string) {
  return REASON_SENTENCES[code] ?? code.toLowerCase().replace(/_/g, " ");
}

export function VerdictCard({ decision }: { decision: EvaluateResponse | null }) {
  if (!decision) {
    return (
      <div className="grid min-h-32 place-items-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-500">
        Verdict pending…
      </div>
    );
  }

  const style = decisionStyles[decision.decision];
  const overridden =
    decision.policyOverrodeAgent && decision.agentProposal && decision.agentProposal !== decision.decision;

  return (
    <div className={`rounded-2xl border p-5 ${style.wrapper}`}>
      <div className="flex items-center gap-3">
        <span className="text-2xl">{style.icon}</span>
        <div>
          <p className={`text-lg font-black uppercase tracking-wide ${style.text}`}>{decision.decision}</p>
          <p className="text-xs font-semibold text-slate-500">Risk tier: {decision.riskTier.toUpperCase()}</p>
        </div>
      </div>

      {overridden && (
        <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl bg-white/70 px-3 py-2 text-xs font-bold text-slate-700">
          Agent proposed <span className="uppercase">{decision.agentProposal}</span>
          <span aria-hidden>→</span>
          Policy decided <span className="uppercase">{decision.decision}</span>
          <span className="ml-1 rounded-full bg-slate-900 px-2 py-0.5 text-[9px] text-white">
            POLICY OVERRODE AGENT
          </span>
        </div>
      )}

      {decision.reasonCodes.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs text-slate-700">
          {decision.reasonCodes.map((code) => (
            <li key={code} className="flex items-start gap-2">
              <span className="mt-1 size-1 shrink-0 rounded-full bg-slate-400" />
              <span>
                {humanize(code)} <span className="text-slate-400">({code})</span>
              </span>
            </li>
          ))}
        </ul>
      )}

      {decision.latencyMs !== null && (
        <p className="mt-3 text-[11px] text-slate-400">Decided in {(decision.latencyMs / 1000).toFixed(1)}s</p>
      )}

      <p className="mt-2 border-t border-current/10 pt-2 text-[10px] font-semibold uppercase tracking-wide opacity-60">
        policy {decision.policyVersion} · audited
      </p>
    </div>
  );
}