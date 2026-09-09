import {
  getNetworkCheckPresentation,
  getTracePresentation,
} from "@/lib/event-presentation";
import type { NetworkCheckPresentation, WsEvent } from "@/lib/types";

const toneStyles: Record<
  NetworkCheckPresentation["tone"],
  { wrapper: string; icon: string; badge: string; symbol: string }
> = {
  success: {
    wrapper: "border-emerald-200 bg-emerald-50/70",
    icon: "bg-emerald-600 text-white",
    badge: "bg-emerald-100 text-emerald-700",
    symbol: "✓",
  },
  danger: {
    wrapper: "border-red-200 bg-red-50/70",
    icon: "bg-red-600 text-white",
    badge: "bg-red-100 text-red-700",
    symbol: "!",
  },
  warning: {
    wrapper: "border-amber-200 bg-amber-50/70",
    icon: "bg-amber-500 text-white",
    badge: "bg-amber-100 text-amber-800",
    symbol: "!",
  },
  progress: {
    wrapper: "border-blue-200 bg-blue-50/70",
    icon: "bg-blue-600 text-white",
    badge: "bg-blue-100 text-blue-700",
    symbol: "•",
  },
};

function NetworkEvent({ event }: { event: WsEvent }) {
  const presentation = getNetworkCheckPresentation(event);
  const style = toneStyles[presentation.tone];

  return (
    <article className={`rounded-2xl border p-3.5 ${style.wrapper}`}>
      <div className="flex items-start gap-3">
        <span
          className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-full text-xs font-bold ${style.icon}`}
        >
          {style.symbol}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold leading-5 text-slate-900">
            {presentation.title}
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-600">
            {presentation.message}
          </p>
          {presentation.details.length > 0 && (
            <ul className="mt-2 space-y-1 border-t border-black/5 pt-2 text-[11px] text-slate-600">
              {presentation.details.map((detail) => (
                <li key={detail}>• {detail}</li>
              ))}
            </ul>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${style.badge}`}>
              {presentation.sourceLabel}
            </span>
            {presentation.latencyMs !== null && (
              <span className="text-[10px] text-slate-400">
                {presentation.latencyMs} ms
              </span>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

function TraceEvent({ event }: { event: WsEvent }) {
  const presentation = getTracePresentation(event);
  return (
    <article className="rounded-2xl border border-blue-100 bg-blue-50/60 p-3.5">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
          ✦
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-bold text-blue-950">{presentation.title}</p>
            {presentation.brain && (
              <span className="rounded-full bg-white/80 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-blue-700">
                {presentation.brain}
              </span>
            )}
          </div>
          <p className="mt-1 text-xs leading-5 text-blue-800/80">
            {presentation.summary}
          </p>
          {presentation.degraded && (
            <p className="mt-2 text-[10px] font-bold text-amber-700">
              Rules fallback used
            </p>
          )}
        </div>
      </div>
    </article>
  );
}

export function StreamEvent({ event }: { event: WsEvent }) {
  if (event.type === "nac.call") return <NetworkEvent event={event} />;
  if (event.type === "agent.trace") return <TraceEvent event={event} />;

  if (event.type === "transaction.started") {
    return (
      <article className="rounded-2xl border border-slate-200 bg-white p-3.5">
        <div className="flex items-center gap-3">
          <span className="grid size-6 place-items-center rounded-full bg-slate-900 text-xs font-bold text-white">
            ✓
          </span>
          <div>
            <p className="text-xs font-bold text-slate-900">Transfer request received</p>
            <p className="mt-0.5 text-[11px] text-slate-500">
              WAKALAH started evaluating the agent&apos;s request.
            </p>
          </div>
        </div>
      </article>
    );
  }

  const title =
    event.type === "mandate.revoked"
      ? "Agent authorization revoked"
      : event.type === "mandate.changed_mid_flight"
        ? "Authorization changed during review"
        : event.type === "mandate.updated"
          ? "Secure authorization ready"
          : null;

  if (!title) return null;

  return (
    <article className="rounded-2xl border border-amber-200 bg-amber-50 p-3.5">
      <p className="text-xs font-bold text-amber-900">{title}</p>
    </article>
  );
}
