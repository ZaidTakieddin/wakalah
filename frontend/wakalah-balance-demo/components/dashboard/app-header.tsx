import { DEMO_AGENT } from "@/lib/demo-data";

export function AppHeader() {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white px-5 py-4 sm:px-8">
      <div className="flex items-center gap-3">
        <div className="grid size-10 place-items-center rounded-xl bg-blue-700 text-sm font-bold text-white shadow-sm">
          B
        </div>
        <div>
          <p className="text-base font-bold tracking-tight text-slate-950">Balance</p>
          <p className="text-xs text-slate-500">Agent-enabled wallet</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-semibold text-slate-900">{DEMO_AGENT.name}</p>
          <p className="text-xs text-slate-500">Authorized payment agent</p>
        </div>
        <div className="grid size-9 place-items-center rounded-full bg-slate-900 text-xs font-bold text-white">
          RA
        </div>
      </div>
    </header>
  );
}
