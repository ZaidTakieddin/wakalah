import type { TransferRecord } from "@/lib/types";

type TransferHistoryProps = {
  transfers: TransferRecord[];
};

const statusStyles: Record<TransferRecord["status"], string> = {
  completed: "bg-emerald-50 text-emerald-700",
  challenge: "bg-amber-50 text-amber-700",
  denied: "bg-red-50 text-red-700",
  failed: "bg-slate-100 text-slate-600",
};

const statusLabels: Record<TransferRecord["status"], string> = {
  completed: "Completed",
  challenge: "Verification required",
  denied: "Blocked",
  failed: "Failed",
};

const amount = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

const date = new Intl.DateTimeFormat("en", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Asia/Qatar",
});

export function TransferHistory({ transfers }: TransferHistoryProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
            Activity
          </p>
          <h2 className="mt-1 text-xl font-bold tracking-tight text-slate-950">
            Transfer history
          </h2>
        </div>
        <span className="text-xs text-slate-500">{transfers.length} records</span>
      </div>

      <div className="mt-5 divide-y divide-slate-100">
        {transfers.map((transfer) => (
          <article
            key={transfer.id}
            className="grid grid-cols-[auto_1fr_auto] items-center gap-3 py-4 first:pt-0 last:pb-0"
          >
            <div className="grid size-10 place-items-center rounded-full bg-slate-100 text-xs font-bold text-slate-700">
              {transfer.beneficiaryName
                .split(" ")
                .slice(0, 2)
                .map((word) => word[0])
                .join("")}
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="truncate text-sm font-bold text-slate-900">
                  {transfer.beneficiaryName}
                </p>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                    transfer.isNewRecipient
                      ? "bg-amber-50 text-amber-700"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {transfer.isNewRecipient ? "New recipient" : "Known recipient"}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {date.format(new Date(transfer.requestedAt))}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-slate-950">
                {transfer.status === "completed" ? "-" : ""}
                {amount.format(transfer.amount)}
              </p>
              <span
                className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold ${statusStyles[transfer.status]}`}
              >
                {statusLabels[transfer.status]}
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
