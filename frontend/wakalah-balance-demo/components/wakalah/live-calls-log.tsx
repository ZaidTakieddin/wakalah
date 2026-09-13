"use client";

import { useEffect, useRef } from "react";
import type { EvaluationRun, WsEvent } from "@/lib/types";

function asRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return value as Record<string, unknown>;
}

function shortPath(path: unknown): string {
  if (typeof path !== "string") return "…";
  return path.replace("/passthrough/camara/v1/", "…/");
}

function shortResponse(response: unknown): string {
  try {
    const text = JSON.stringify(response);
    return text.length > 140 ? `${text.slice(0, 140)}…` : text;
  } catch {
    return "…";
  }
}

/** The permanent proof panel: every CAMARA call, every run, newest at the
 *  bottom, auto-scrolling. All runtime calls are POST. */
export function LiveCallsLog({ runs }: { runs: EvaluationRun[] }) {
  const calls: WsEvent[] = runs.flatMap((run) => run.events).filter(
    (event) => event.type === "nac.call",
  );
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = scrollRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [calls.length]);

  return (
    <section aria-label="Live CAMARA calls" className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
          Live CAMARA calls · Nokia NaC
        </p>
        <span className="grid size-7 place-items-center rounded-full bg-slate-100 text-[11px] font-bold text-slate-600">
          {calls.length}
        </span>
      </div>
      <div
        ref={scrollRef}
        className="mt-3 max-h-72 min-h-24 space-y-1.5 overflow-y-auto rounded-xl bg-slate-950 p-3 font-mono"
      >
        {calls.length === 0 ? (
          <p className="text-[11px] text-slate-500">
            No network calls yet — run a beat and watch them arrive live.
          </p>
        ) : (
          calls.map((event, index) => {
            const payload = asRecord(event.payload);
            const status = payload.status;
            const failed = typeof status === "number" && status >= 400;
            const latency = payload.latencyMs;
            return (
              <div key={`${event.ts}-${index}`} className="text-[11px] leading-5">
                <p className={failed ? "text-amber-400" : "text-slate-200"}>
                  POST {shortPath(payload.path)}{" "}
                  <span className={failed ? "font-bold text-amber-300" : "text-slate-400"}>
                    {typeof status === "number" ? status : "…"}
                  </span>{" "}
                  <span className="text-slate-500">
                    {typeof latency === "number" ? `${latency} ms` : ""} ·{" "}
                    {typeof payload.source === "string" ? payload.source : ""}
                  </span>
                </p>
                <p className="truncate text-slate-500">→ {shortResponse(payload.response)}</p>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
