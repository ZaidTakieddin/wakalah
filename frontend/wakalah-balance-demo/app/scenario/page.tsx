"use client";

import { useState } from "react";

import { RecentStrip } from "@/components/scenario/recent-strip";
import { ScenarioRunner } from "@/components/scenario/scenario-runner";
import { StatusBar } from "@/components/scenario/status-bar";
import { LiveCallsLog } from "@/components/wakalah/live-calls-log";
import { ScenarioLivePanel } from "@/components/wakalah/scenario-live-panel";
import { useWakalahRuns } from "@/hooks/use-wakalah-runs";


export default function ScenarioPage() {
  const {
    runs,
    activeTransactionId,
    mandateStatus,
    connectionStatus,
    activeBeat,
    revocation,
  } = useWakalahRuns();
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [lastAutoExpanded, setLastAutoExpanded] = useState<string | null>(null);

  // Auto-expand the active run. Adjusted during render (not in an effect) so
  // a manual collapse while the run is active is respected afterwards.
  if (activeTransactionId !== lastAutoExpanded) {
    setLastAutoExpanded(activeTransactionId);
    if (activeTransactionId) setExpandedRunId(activeTransactionId);
  }

  return (
    <main className="min-h-screen bg-[#f5f7fb] text-slate-950">
      <div className="mx-auto max-w-385 space-y-5 p-4 sm:p-5">
        <StatusBar connectionStatus={connectionStatus} />

        {revocation && (
          <div
            role="alert"
            className="rounded-2xl border border-red-300 bg-red-600 p-4 text-white shadow-lg"
          >
            <p className="text-sm font-black uppercase tracking-wide">
              ⛔ Agent authorization revoked
            </p>
            <p className="mt-1 text-xs leading-5 text-red-100">
              {revocation.kind === "mid_flight" &&
              revocation.verdictBefore &&
              revocation.verdictNow
                ? `Verdict changed mid-transaction: ${revocation.verdictBefore.toUpperCase()} → ${revocation.verdictNow.toUpperCase()} — revocation landed while the decision was still being made.`
                : `Mandate ${revocation.mandateId ?? "active"} revoked${
                    revocation.reason ? ` (${revocation.reason})` : ""
                  }. Every outstanding authorization is dead.`}
            </p>
          </div>
        )}

        {activeBeat && (
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
              Now playing · {activeBeat.title}
            </p>
            <p className="mt-1 text-sm leading-6 text-slate-800">{activeBeat.narration}</p>
            {activeBeat.expect && (
              <p className="mt-1 text-xs text-slate-500">
                Watch for: {activeBeat.expect}
              </p>
            )}
            {activeBeat.labels.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {activeBeat.labels.map((label) => (
                  <span
                    key={label}
                    className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500"
                  >
                    {label}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        <RecentStrip runs={runs} />

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_460px]">
          <div className="min-w-0">
            <ScenarioRunner />
          </div>

          <ScenarioLivePanel
            runs={runs}
            expandedRunId={expandedRunId}
            mandateStatus={mandateStatus}
            onToggleRun={(id) => setExpandedRunId((cur) => (cur === id ? null : id))}
          />
        </div>

        <LiveCallsLog runs={runs} />
      </div>
    </main>
  );
}