"use client";

import { useEffect, useState } from "react";

import { ScenarioRunner } from "@/components/scenario/scenario-runner";
import { ScenarioLivePanel } from "@/components/wakalah/scenario-live-panel";
import { useWakalahRuns } from "@/hooks/use-wakalah-runs";


export default function ScenarioPage() {
  const { runs, activeTransactionId, mandateStatus } = useWakalahRuns();
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  useEffect(() => {
    if (activeTransactionId) setExpandedRunId(activeTransactionId);
  }, [activeTransactionId]);

  return (
    <main className="min-h-screen bg-[#f5f7fb] text-slate-950">
      <div className="mx-auto grid max-w-385 gap-5 p-4 sm:p-5 xl:grid-cols-[minmax(0,1fr)_460px]">
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
    </main>
  );
}