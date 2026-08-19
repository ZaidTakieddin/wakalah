import { StreamEvent } from "@/components/wakalah/stream-event";
import type { Decision, EvaluationRun } from "@/lib/types";

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

const decisionStyles: Record<Decision, string> = {
  allow: "border-emerald-200 bg-emerald-50 text-emerald-800",
  challenge: "border-amber-200 bg-amber-50 text-amber-800",
  deny: "border-red-200 bg-red-50 text-red-800",
};

const decisionMessages: Record<Decision, string> = {
  allow: "The policy approved this transfer.",
  challenge: "Additional verification is required before money can move.",
  deny: "The policy blocked this transfer.",
};

export function EvaluationRunCard({
  run,
  expanded,
  onToggle,
}: EvaluationRunCardProps) {
  const visibleEvents = run.events.filter(
    (event) => event.type !== "decision.final" && event.type !== "scenario.reset",
  );

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
          <span className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
            {run.status === "running"
              ? "Evaluating"
              : run.decision?.decision ?? run.status}
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
            {visibleEvents.map((event, index) => (
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

            {run.decision && (
              <div
                className={`rounded-2xl border p-4 ${decisionStyles[run.decision.decision]}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.14em] opacity-70">
                      Final policy decision
                    </p>
                    <p className="mt-1 text-xl font-black uppercase tracking-tight">
                      {run.decision.decision}
                    </p>
                  </div>
                  <span className="rounded-full bg-white/70 px-2.5 py-1 text-[10px] font-bold uppercase">
                    {run.decision.riskTier} risk
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 opacity-90">
                  {decisionMessages[run.decision.decision]}
                </p>
                {run.decision.policyOverrodeAgent && (
                  <p className="mt-2 border-t border-current/10 pt-2 text-[11px] font-bold">
                    Policy overrode the AI recommendation.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </article>
  );
}
