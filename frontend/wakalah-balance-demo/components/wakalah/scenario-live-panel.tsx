"use client";

import { useEffect, useRef } from "react";
import { EvaluationRunCard } from "@/components/wakalah/evaluation-run-card";
import type { EvaluationRun, MandateStatus } from "@/lib/types";

type LivePanelProps = {
  runs: EvaluationRun[];
  expandedRunId: string | null;
  onToggleRun: (transactionId: string) => void;
  mandateStatus: MandateStatus;
};

const MANDATE_CONFIG: Record<
MandateStatus ,
  { label: string; dot: string; pill: string; pulse?: boolean }
> = {
  idle: {
    label: "No mandate",
    dot: "bg-slate-400",
    pill: "border-white/10 bg-white/5 text-slate-300",
  },
  loading: {
    label: "Checking mandate",
    dot: "bg-amber-400",
    pill: "border-amber-400/20 bg-amber-400/10 text-amber-300",
    pulse: true,
  },
  success: {
    label: "Mandate active",
    dot: "bg-emerald-400",
    pill: "border-emerald-400/20 bg-emerald-400/10 text-emerald-300",
    pulse: true,
  },
  error: {
    label: "Mandate inactive",
    dot: "bg-rose-400",
    pill: "border-rose-400/20 bg-rose-400/10 text-rose-300",
  },
};

export function ScenarioLivePanel({
  runs,
  expandedRunId,
  onToggleRun,
  mandateStatus,
}: LivePanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef(new Map<string, HTMLDivElement>());
  const topRunIdRef = useRef<string | null>(null);

  useEffect(() => {
    const currentTopId = runs[0]?.transactionId ?? null;
    if (currentTopId && currentTopId !== topRunIdRef.current) {
      scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
    }
    topRunIdRef.current = currentTopId;
  }, [runs]);

  const expandedRun = runs.find((run) => run.transactionId === expandedRunId);
  const expandedEventCount = expandedRun?.events.length ?? 0;

  useEffect(() => {
    if (!expandedRunId) return;
    const node = cardRefs.current.get(expandedRunId);
    node?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [expandedRunId, expandedEventCount]);

  const mandate = MANDATE_CONFIG[mandateStatus];

  return (
    <aside className="flex min-h-[640px] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_18px_50px_-32px_rgba(15,23,42,0.6)] xl:sticky xl:top-5 xl:h-[calc(100vh-2.5rem)]">
      <header className="border-b border-slate-200 bg-slate-950 px-5 py-5 text-white">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-blue-600 text-sm font-black">
              W
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-wide">WAKALAH</h2>
              <p className="mt-0.5 text-[11px] text-slate-400">Live trust stream</p>
            </div>
          </div>

          <div
            className={`flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-semibold ${mandate.pill}`}
          >
            <span className="relative flex size-1.5">
              {mandate.pulse && (
                <span
                  className={`absolute inline-flex size-full animate-ping rounded-full ${mandate.dot} opacity-75`}
                />
              )}
              <span className={`relative inline-flex size-1.5 rounded-full ${mandate.dot}`} />
            </span>
            {mandate.label}
          </div>
        </div>
      </header>
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="flex items-center justify-between px-5 pb-3 pt-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
              Evaluations
            </p>
            <p className="mt-1 text-[11px] text-slate-400">
              Previous streams stay available
            </p>
          </div>
          <span className="grid size-7 place-items-center rounded-full bg-slate-100 text-[11px] font-bold text-slate-600">
            {runs.length}
          </span>
        </div>

        <div
          ref={scrollRef}
          className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 pb-4"
        >
          {runs.length === 0 ? (
            <div className="grid min-h-48 place-items-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-center">
              <div>
                <div className="mx-auto grid size-10 place-items-center rounded-full bg-white text-lg shadow-sm">
                  ◌
                </div>
                <p className="mt-3 text-sm font-bold text-slate-700">No activity yet</p>
                <p className="mt-1 max-w-56 text-xs leading-5 text-slate-500">
                  A live decision stream will appear when the agent requests a transfer.
                </p>
              </div>
            </div>
          ) : (
            runs.map((run) => (
              <div
                key={run.transactionId}
                ref={(node) => {
                  if (node) cardRefs.current.set(run.transactionId, node);
                  else cardRefs.current.delete(run.transactionId);
                }}
              >
                <EvaluationRunCard
                  run={run}
                  expanded={expandedRunId === run.transactionId}
                  onToggle={() => onToggleRun(run.transactionId)}
                />
              </div>
            ))
          )}
        </div>
      </div>
    </aside>
  );
}