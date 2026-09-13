import { Loader2 } from "lucide-react";
import { DecisionPipeline } from "@/components/scenario/decision-pipeline";
import { VerdictCard } from "@/components/scenario/verdict-card";
import { EvidenceGrid } from "@/components/wakalah/evidence-grid";
import { StreamEvent } from "@/components/wakalah/stream-event";
import type { EvaluationRun } from "@/lib/types";

type EvaluationRunCardProps = {
  run: EvaluationRun;
  expanded: boolean;
  onToggle: () => void;
};

const amount = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

// Chip styling for the collapsed header. Keys are "running" / "failed" plus
// the three Decision values, so both in-flight and terminal states get a
// color that matches the eventual verdict card below.
const statusChipStyles: Record<string, string> = {
  running: "bg-blue-100 text-blue-700",
  allow: "bg-emerald-100 text-emerald-700",
  challenge: "bg-amber-100 text-amber-700",
  deny: "bg-red-100 text-red-700",
  failed: "bg-red-100 text-red-700",
};

function statusChipKey(run: EvaluationRun): keyof typeof statusChipStyles {
  if (run.status === "running") return "running";
  if (run.status === "failed") return "failed";
  return run.decision?.decision ?? "challenge";
}

function statusChipLabel(run: EvaluationRun) {
  if (run.status === "running") return "Evaluating";
  if (run.status === "failed") return "Failed";
  return run.decision?.decision ?? run.status;
}

export function EvaluationRunCard({
  run,
  expanded,
  onToggle,
}: EvaluationRunCardProps) {
  const visibleEvents = run.events.filter(
    (event) => event.type !== "decision.final" && event.type !== "scenario.reset",
  );
  const chipKey = statusChipKey(run);

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className="flex w-full items-start justify-between gap-3 p-4 text-left transition hover:bg-slate-50"
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`size-2 rounded-full ${
                run.status === "running"
                  ? "animate-pulse bg-blue-500"
                  : run.status === "failed"
                    ? "bg-red-500"
                    : "bg-emerald-500"
              }`}
            />
            <p className="truncate text-xs font-bold text-slate-900">{run.action}</p>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            {run.phoneNumber} · {amount.format(run.amount)}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${statusChipStyles[chipKey]}`}
          >
            {run.status === "running" && <Loader2 className="h-3 w-3 animate-spin" />}
            {statusChipLabel(run)}
          </span>
          <span className={`text-sm text-slate-400 transition ${expanded ? "rotate-180" : ""}`}>
            ⌄
          </span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50/60 p-3">
          <div className="mb-3 rounded-xl bg-slate-900 p-3 text-white">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
              Agent action
            </p>
            <p className="mt-1 text-xs font-semibold leading-5">{run.action}</p>
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-slate-400">
              <span>{run.phoneNumber}</span>
              <span>{run.transactionId.slice(0, 18)}…</span>
              <span>{run.isNewRecipient ? "New recipient" : "Known recipient"}</span>
            </div>
          </div>

          <div className="space-y-2.5">
            <DecisionPipeline events={run.events} />
            {visibleEvents
              .filter((event) => event.type !== "agent.trace")
              .map((event, index) => (
                <StreamEvent key={`${event.ts}-${event.type}-${index}`} event={event} />
              ))}

            {run.status === "running" && visibleEvents.length === 0 && (
              <div className="flex items-center gap-3 rounded-xl border border-blue-100 bg-blue-50 p-3 text-xs text-blue-800">
                <span className="size-4 animate-spin rounded-full border-2 border-blue-200 border-t-blue-700" />
                Waiting for WAKALAH events…
              </div>
            )}

            {run.error && (
              <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs leading-5 text-red-700">
                {run.error}
              </div>
            )}

            <VerdictCard decision={run.decision} />
            {run.decision && Object.keys(run.decision.evidenceSummary ?? {}).length > 0 && (
              <EvidenceGrid evidenceSummary={run.decision.evidenceSummary ?? {}} />
            )}
          </div>
        </div>
      )}
    </article>
  );
}