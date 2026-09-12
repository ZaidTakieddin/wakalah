"use client";

import { getTracePresentation } from "@/lib/event-presentation";
import type { WsEvent } from "@/lib/types";

const POLICY_STEPS = new Set(["enforce_floor", "decide"]);

export function DecisionPipeline({ events }: { events: WsEvent[] }) {
  const traceEvents = events.filter((e) => e.type === "agent.trace");

  if (traceEvents.length === 0) {
    return (
      <div className="grid min-h-40 place-items-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-500">
        Waiting for the agent to start reasoning…
      </div>
    );
  }

  return (
    <ol className="space-y-2">
      {traceEvents.map((event, i) => {
        const presentation = getTracePresentation(event);
        const payload = (event.payload ?? {}) as Record<string, unknown>;
        const isPolicy = POLICY_STEPS.has(String(payload.step ?? ""));

        return (
          <li
            key={`${event.type}-${event.ts}-${i}`}
            className={`flex items-start gap-3 rounded-2xl border p-3.5 ${
              isPolicy ? "border-violet-200 bg-violet-50/70" : "border-blue-200 bg-blue-50/70"
            }`}
          >
            <span
              className={`mt-0.5 grid size-7 shrink-0 place-items-center rounded-full text-sm ${
                isPolicy ? "bg-violet-600 text-white" : "bg-blue-600 text-white"
              }`}
            >
              {isPolicy ? "⚖️" : "🧠"}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className={`text-xs font-bold ${isPolicy ? "text-violet-950" : "text-blue-950"}`}>
                  {presentation.title}
                </p>
                <span
                  className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide ${
                    isPolicy ? "bg-violet-100 text-violet-700" : "bg-white/80 text-blue-700"
                  }`}
                >
                  {isPolicy ? "policy" : "agent"}
                </span>
                {presentation.brain && (
                  <span className="rounded-full bg-white/80 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-slate-500">
                    {presentation.brain}
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs leading-5 text-slate-700">{presentation.summary}</p>
              {presentation.degraded && (
                <p className="mt-1 text-[10px] font-bold text-amber-700">Fallback rules used</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}