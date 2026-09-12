"use client";

import type { EvaluationRun } from "@/lib/types";

const verdictStyles: Record<string, { badge: string; symbol: string }> = {
  allow: { badge: "bg-emerald-100 text-emerald-700", symbol: "✅" },
  challenge: { badge: "bg-amber-100 text-amber-700", symbol: "⚠️" },
  deny: { badge: "bg-red-100 text-red-700", symbol: "⛔" },
};

export function RecentStrip({ runs }: { runs: EvaluationRun[] }) {
  const finished = runs.filter((run) => run.status !== "running").slice(0, 3);
  if (finished.length === 0) return null;

  return (
    <section
      aria-label="Recent decisions"
      className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3"
    >
      <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
        Recent
      </p>
      {finished.map((run) => {
        const verdict = run.decision?.decision ?? "challenge";
        const style = verdictStyles[verdict] ?? verdictStyles.challenge;
        const checks = run.events.filter((e) => e.type === "nac.call").length;
        return (
          <span
            key={run.transactionId}
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold ${style.badge}`}
            title={run.action}
          >
            <span aria-hidden>{style.symbol}</span>
            {checks} check{checks === 1 ? "" : "s"}
          </span>
        );
      })}
    </section>
  );
}
