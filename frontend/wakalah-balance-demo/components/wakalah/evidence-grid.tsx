"use client";

import {
  DIMENSION_LABELS,
  DIMENSION_ORDER,
  type TrustDimension,
} from "@/lib/signal-dimensions";
import type { SignalEvidence } from "@/lib/types";

function humanizeSignal(name: string): string {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

const stateStyles: Record<"clean" | "risk" | "unknown", string> = {
  clean: "border-emerald-200 bg-emerald-50/60",
  risk: "border-red-200 bg-red-50/60",
  unknown: "border-slate-200 bg-slate-50",
};

function signalState(evidence: SignalEvidence): "clean" | "risk" | "unknown" {
  if (!evidence.available) return "unknown";
  // Mirrors the policy engine's own reading: these are exactly the findings
  // its rules fire on. Tenure and roaming have no rules — informational only.
  const r = evidence.result;
  const risky =
    r["swapped"] === true ||
    r["forwarding_active"] === true ||
    r["recycled"] === true ||
    r["any_mismatch"] === true ||
    r["reachable"] === false ||
    r["number_verified"] === false ||
    r["in_expected_area"] === false;
  return risky ? "risk" : "clean";
}

export function EvidenceGrid({
  evidenceSummary,
}: {
  evidenceSummary: Record<string, SignalEvidence>;
}) {
  const names = Object.keys(evidenceSummary);
  if (names.length === 0) return null;

  const byDimension = new Map<TrustDimension, string[]>();
  for (const name of names) {
    const dimension = (evidenceSummary[name]?.dimension ?? "context") as TrustDimension;
    const list = byDimension.get(dimension) ?? [];
    list.push(name);
    byDimension.set(dimension, list);
  }

  return (
    <div className="space-y-2.5">
      {DIMENSION_ORDER.filter((dimension) => byDimension.has(dimension)).map(
        (dimension) => (
          <div key={dimension} className="rounded-2xl border border-slate-200 bg-white p-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
              {DIMENSION_LABELS[dimension]}
            </p>
            <div className="mt-2 space-y-1.5">
              {(byDimension.get(dimension) ?? []).map((name) => {
                const evidence = evidenceSummary[name];
                if (!evidence) return null;
                const state = signalState(evidence);
                return (
                  <div
                    key={name}
                    className={`flex flex-wrap items-center justify-between gap-2 rounded-xl border px-2.5 py-1.5 ${stateStyles[state]}`}
                  >
                    <span className="text-[11px] font-bold text-slate-800">
                      {humanizeSignal(name)}
                    </span>
                    <span className="flex items-center gap-2">
                      {!evidence.available && evidence.errorCode && (
                        <span className="text-[10px] text-slate-500">{evidence.errorCode}</span>
                      )}
                      <span className="rounded-full bg-white/80 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-slate-600">
                        {evidence.source}
                      </span>
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ),
      )}
    </div>
  );
}
