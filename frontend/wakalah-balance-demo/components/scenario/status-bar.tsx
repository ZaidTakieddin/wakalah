"use client";

import { useEffect, useState } from "react";
import { getHealth, type BackendHealth } from "@/actions/wakalah";
import type { ConnectionStatus } from "@/lib/types";

const dotStyles: Record<ConnectionStatus, string> = {
  connecting: "animate-pulse bg-blue-400",
  connected: "bg-emerald-400",
  disconnected: "animate-pulse bg-amber-400",
};

export function StatusBar({ connectionStatus }: { connectionStatus: ConnectionStatus }) {
  const [health, setHealth] = useState<BackendHealth | null>(null);

  useEffect(() => {
    let cancelled = false;
    void getHealth().then((result) => {
      if (!cancelled && result.ok) setHealth(result.data);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const degraded = health !== null && health.audit_backend.startsWith("memory");

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-xs">
      <span className="flex items-center gap-2 font-bold text-slate-700">
        <span className={`size-2 rounded-full ${dotStyles[connectionStatus]}`} />
        {connectionStatus === "connected"
          ? "Live"
          : connectionStatus === "connecting"
            ? "Connecting"
            : "Reconnecting"}
      </span>
      {health ? (
        <>
          <span className="text-slate-400">brains: {health.brains_configured[0] ?? "none"}</span>
          <span className="text-slate-400">policy {health.policy_version}</span>
          <span className="text-slate-400">evidence: {health.nac_mode}</span>
          {degraded ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800">
              DEGRADED · audit in memory
            </span>
          ) : (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
              audited
            </span>
          )}
        </>
      ) : (
        <span className="text-slate-400">reaching backend…</span>
      )}
    </div>
  );
}
