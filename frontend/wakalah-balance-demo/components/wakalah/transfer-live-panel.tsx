import { EvaluationRunCard } from "@/components/wakalah/evaluation-run-card";
import { MandateStatus } from "@/components/wakalah/mandate-status";
import type {
  ConnectionStatus,
  EvaluationRun,
  MandateStatus as MandateState,
} from "@/lib/types";

type LivePanelProps = {
  phoneNumber: string;
  mandateStatus: MandateState;
  mandateError: string | null;
  connectionStatus: ConnectionStatus;
  runs: EvaluationRun[];
  expandedRunId: string | null;
  isEvaluating: boolean;
  onSetPhone: () => void;
  onRetryMandate: () => void;
  onToggleRun: (transactionId: string) => void;
};

const connectionLabels: Record<ConnectionStatus, string> = {
  connecting: "Connecting",
  connected: "Live",
  disconnected: "Reconnecting",
};

export function TransferLivePanel({
  phoneNumber,
  mandateStatus,
  mandateError,
  connectionStatus,
  runs,
  expandedRunId,
  isEvaluating,
  onSetPhone,
  onRetryMandate,
  onToggleRun,
}: LivePanelProps) {
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
          <span className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold text-slate-300">
            <span
              className={`size-1.5 rounded-full ${
                connectionStatus === "connected"
                  ? "bg-emerald-400"
                  : connectionStatus === "connecting"
                    ? "animate-pulse bg-blue-400"
                    : "animate-pulse bg-amber-400"
              }`}
            />
            {connectionLabels[connectionStatus]}
          </span>
        </div>
      </header>

      <div className="border-b border-slate-100 p-4">
        <MandateStatus
          status={mandateStatus}
          phoneNumber={phoneNumber}
          error={mandateError}
          disabled={isEvaluating}
          onSetPhone={onSetPhone}
          onRetry={onRetryMandate}
        />
      </div>

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

        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 pb-4">
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
              <EvaluationRunCard
                key={run.transactionId}
                run={run}
                expanded={expandedRunId === run.transactionId}
                onToggle={() => onToggleRun(run.transactionId)}
              />
            ))
          )}
        </div>
      </div>
    </aside>
  );
}
