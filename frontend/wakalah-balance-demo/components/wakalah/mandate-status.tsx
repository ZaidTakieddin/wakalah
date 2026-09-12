import type { MandateStatus as MandateState } from "@/lib/types";

type MandateStatusProps = {
  status: MandateState;
  phoneNumber: string;
  error: string | null;
  disabled: boolean;
  onSetPhone: () => void;
  onRetry: () => void;
};

export function MandateStatus({
  status,
  phoneNumber,
  error,
  disabled,
  onSetPhone,
  onRetry,
}: MandateStatusProps) {
  if (status === "idle") {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-center">
        <div className="mx-auto grid size-10 place-items-center rounded-full bg-slate-200 text-lg text-slate-600">
          !
        </div>
        <p className="mt-3 text-sm font-bold text-slate-800">
          Secure transactions are disabled
        </p>
        <p className="mt-1 text-xs leading-5 text-slate-500">
          Set your phone number to activate WAKALAH protection.
        </p>
        <button
          type="button"
          onClick={onSetPhone}
          className="mt-4 h-10 rounded-xl bg-slate-950 px-4 text-xs font-bold text-white transition hover:bg-slate-800"
        >
          Set phone number
        </button>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div
        className="flex items-center gap-3 rounded-2xl border border-blue-100 bg-blue-50 p-4"
        aria-live="polite"
      >
        <span className="size-5 shrink-0 animate-spin rounded-full border-2 border-blue-200 border-t-blue-700" />
        <div>
          <p className="text-sm font-bold text-blue-950">Setting up secure access</p>
          <p className="mt-0.5 text-xs leading-5 text-blue-700/80">
            Preparing your account for secure transactions...
          </p>
        </div>
      </div>
    );
  } 

  if (status === "error") {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-4" role="alert">
        <div className="flex items-start gap-3">
          <span className="grid size-6 shrink-0 place-items-center rounded-full bg-red-100 text-xs font-bold text-red-700">
            ×
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-red-900">Secure setup failed</p>
            <p className="mt-1 text-xs leading-5 text-red-700">
              {error ?? "WAKALAH could not prepare this account."}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 h-9 w-full rounded-xl bg-red-700 px-4 text-xs font-bold text-white transition hover:bg-red-800"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
      <div className="flex items-start gap-3">
        <span className="grid size-6 shrink-0 place-items-center rounded-full bg-emerald-600 text-xs font-bold text-white">
          ✓
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-emerald-950">
            Secure transaction protection is active
          </p>
          <p className="mt-1 truncate text-xs text-emerald-700">{phoneNumber}</p>
        </div>
        <button
          type="button"
          onClick={onSetPhone}
          disabled={disabled}
          className="text-xs font-bold text-emerald-800 underline-offset-2 hover:underline disabled:cursor-not-allowed disabled:opacity-40"
        >
          Change
        </button>
      </div>
    </div>
  );
}
