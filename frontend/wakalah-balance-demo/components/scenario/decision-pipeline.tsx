"use client";

import { getTracePresentation } from "@/lib/event-presentation";
import type { WsEvent } from "@/lib/types";

type NodeKind = "agent" | "policy" | "tools";
type NodeState = "idle" | "running" | "done";

type NodeDef = {
  step: string;
  label: string;
  icon: string;
  kind: NodeKind;
};

const NODES: NodeDef[] = [
  { step: "classify_risk", label: "Classify", icon: "🧠", kind: "agent" },
  { step: "build_plan", label: "Plan", icon: "🧠", kind: "agent" },
  { step: "enforce_floor", label: "Floor", icon: "⚖️", kind: "policy" },
  { step: "gather_evidence", label: "Gather", icon: "🔌", kind: "tools" },
  { step: "interpret", label: "Interp", icon: "🧠", kind: "agent" },
  { step: "decide", label: "Decide", icon: "⚖️", kind: "policy" },
];

function asRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return value as Record<string, unknown>;
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

/** Headline per node, read off the supervisor's native snake_case detail keys. */
function headline(
  step: string,
  detail: Record<string, unknown>,
  summary: string | null,
): string | null {
  switch (step) {
    case "classify_risk": {
      const tier = detail.agent_tier;
      return typeof tier === "string" ? tier.toUpperCase() : null;
    }
    case "build_plan": {
      const signals = asArray(detail.signals);
      return `${signals.length} check${signals.length === 1 ? "" : "s"}`;
    }
    case "enforce_floor": {
      const added = asArray(detail.added_by_policy);
      return added.length > 0 ? `+${added.length} added` : "floor met";
    }
    case "gather_evidence": {
      const results = asRecord(detail.results);
      const names = Object.keys(results);
      const usable = names.filter((name) => {
        const entry = asRecord(results[name]);
        return !("error" in entry) && !("unavailable" in entry);
      }).length;
      return names.length > 0 ? `${usable}/${names.length}` : null;
    }
    case "interpret": {
      // No verdict key in detail — the summary carries it ("Agent proposes X").
      const match = summary?.match(/proposes\s+([A-Z_]+)/i);
      return match ? match[1].toUpperCase() : null;
    }
    case "decide": {
      const verdict = detail.verdict;
      return typeof verdict === "string" ? verdict.toUpperCase() : null;
    }
    default:
      return null;
  }
}

function rationaleOf(detail: Record<string, unknown>): string | null {
  return typeof detail.rationale === "string" && detail.rationale.length > 0
    ? detail.rationale
    : null;
}

const kindStyles: Record<NodeKind, { border: string; icon: string; chip: string; label: string }> = {
  agent: {
    border: "border-blue-200 bg-blue-50/70",
    icon: "bg-blue-600 text-white",
    chip: "bg-white/80 text-blue-700",
    label: "agent",
  },
  policy: {
    border: "border-violet-200 bg-violet-50/70",
    icon: "bg-violet-600 text-white",
    chip: "bg-violet-100 text-violet-700",
    label: "policy",
  },
  tools: {
    border: "border-slate-200 bg-slate-50/70",
    icon: "bg-slate-600 text-white",
    chip: "bg-white/80 text-slate-600",
    label: "tools",
  },
};

export function DecisionPipeline({ events }: { events: WsEvent[] }) {
  const byStep = new Map<string, WsEvent>();
  for (const event of events) {
    if (event.type !== "agent.trace") continue;
    const step = String(asRecord(event.payload).step ?? "");
    if (step && !byStep.has(step)) byStep.set(step, event);
  }

  const checksRun = events.filter((e) => e.type === "nac.call").length;
  const lastArrived = NODES.map((node) => node.step).filter((step) => byStep.has(step)).length;

  const lastRationale =
    [...byStep.values()]
      .map((event) => rationaleOf(asRecord(event.payload)))
      .findLast((rationale) => rationale !== null) ?? null;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
          Decision pipeline
        </p>
        <p className="text-xs font-black text-slate-900">
          checks run: {checksRun}
        </p>
      </div>

      {byStep.size === 0 && (
        <div className="grid min-h-24 place-items-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
          Waiting for the agent to start reasoning…
        </div>
      )}

      <ol className="space-y-2">
        {NODES.map((node, index) => {
          const event = byStep.get(node.step);
          const state: NodeState = event
            ? "done"
            : index === lastArrived
              ? "running"
              : "idle";
          if (!event && state === "idle") {
            return (
              <li
                key={node.step}
                className="flex items-center gap-3 rounded-2xl border border-dashed border-slate-200 p-3 opacity-60"
              >
                <span className="grid size-7 shrink-0 place-items-center rounded-full bg-slate-100 text-sm">
                  {node.icon}
                </span>
                <p className="text-xs font-bold text-slate-400">{node.label}</p>
              </li>
            );
          }

          const payload = asRecord(event?.payload);
          const detail = asRecord(payload.detail);
          const presentation = event ? getTracePresentation(event) : null;
          const style = kindStyles[node.kind];
          const head = headline(node.step, detail, presentation?.summary ?? null);
          const overridden =
            node.step === "decide" && detail.policy_overrode_agent === true;
          const floorAdded =
            node.step === "enforce_floor" && asArray(detail.added_by_policy).length > 0;

          return (
            <li
              key={node.step}
              className={`flex items-start gap-3 rounded-2xl border p-3.5 ${style.border} ${
                state === "running" ? "animate-pulse" : ""
              }`}
            >
              <span
                className={`mt-0.5 grid size-7 shrink-0 place-items-center rounded-full text-sm ${style.icon}`}
              >
                {node.icon}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-xs font-bold text-slate-900">
                    {presentation?.title ?? node.label}
                    {head ? <span className="text-slate-500"> · {head}</span> : null}
                  </p>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide ${style.chip}`}
                  >
                    {state === "running" ? "running" : style.label}
                  </span>
                  {presentation?.brain && (
                    <span className="rounded-full bg-white/80 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-slate-500">
                      {presentation.brain}
                    </span>
                  )}
                  {floorAdded && (
                    <span className="rounded-full bg-violet-600 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white">
                      floor added checks
                    </span>
                  )}
                  {overridden && (
                    <span className="rounded-full bg-slate-900 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white">
                      overrode agent
                    </span>
                  )}
                </div>
                {presentation && (
                  <p className="mt-1 text-xs leading-5 text-slate-700">
                    {presentation.summary}
                  </p>
                )}
                {presentation?.degraded && (
                  <p className="mt-1 text-[10px] font-bold text-amber-700">
                    Fallback rules used
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>

      {lastRationale && (
        <p className="mt-2 text-xs leading-5 text-slate-500">▸ {lastRationale}</p>
      )}
    </div>
  );
}
