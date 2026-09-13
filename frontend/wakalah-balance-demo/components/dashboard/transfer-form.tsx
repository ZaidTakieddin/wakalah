"use client";

import type { FormEvent } from "react";
import {
  DEMO_AGENT,
  DEMO_SCRIPT_HINTS,
  MANDATE_LIMIT,
  NEW_RECIPIENT_SUGGESTION,
  PERSONAS,
} from "@/lib/demo-data";
import type { MandateStatus } from "@/lib/types";

type TransferFormProps = {
  recipientName: string;
  recipientOptions: string[];
  amount: string;
  note: string;
  mandateStatus: MandateStatus;
  isEvaluating: boolean;
  isNewRecipient: boolean;
  phoneNumber: string;
  onRecipientChange: (name: string) => void;
  onAmountChange: (amount: string) => void;
  onNoteChange: (note: string) => void;
  onSubmit: () => void;
  onPhoneSelect: (phoneNumber: string) => void;
};

export function TransferForm({
  recipientName,
  recipientOptions,
  amount,
  note,
  mandateStatus,
  isEvaluating,
  isNewRecipient,
  phoneNumber,
  onRecipientChange,
  onAmountChange,
  onNoteChange,
  onSubmit,
  onPhoneSelect,
}: TransferFormProps) {
  const amountValue = Number(amount);
  const invalidAmount =
    !Number.isFinite(amountValue) ||
    amountValue <= 0 ||
    amountValue > MANDATE_LIMIT;
  const invalidRecipient = recipientName.trim().length === 0;
  const isReady = mandateStatus === "success";
  const disabled =
    !isReady || isEvaluating || invalidAmount || invalidRecipient;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!disabled) onSubmit();
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.5)] sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-700">
            New transfer
          </p>
          <h2 className="mt-1 text-xl font-bold tracking-tight text-slate-950">
            Send money
          </h2>
        </div>
        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
          Requested by {DEMO_AGENT.name}
        </span>
      </div>

      <div className="mt-6">
        <span className="text-sm font-semibold text-slate-800">Phone number</span>
        <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4" role="group" aria-label="Sandbox persona">
          {PERSONAS.map((persona) => {
            const selected = phoneNumber === persona.value;
            return (
              <button
                key={persona.value}
                type="button"
                title={`${persona.value} — ${persona.description}`}
                onClick={() => onPhoneSelect(persona.value)}
                disabled={isEvaluating}
                aria-pressed={selected}
                className={`h-11 rounded-xl border px-2 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                  selected
                    ? "border-blue-700 bg-blue-700 text-white shadow-sm"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                {persona.short}
              </button>
            );
          })}
        </div>
        <p className="mt-1.5 text-xs text-slate-500">
          {mandateStatus === "loading"
            ? "Activating secure transactions…"
            : "Pick a number — protection activates instantly."}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        <label className="block">
          <span className="text-sm font-semibold text-slate-800">Recipient</span>
          <select
            value={recipientName}
            onChange={(event) => onRecipientChange(event.target.value)}
            disabled={isEvaluating}
            className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-50"
          >
            {[...recipientOptions, NEW_RECIPIENT_SUGGESTION].map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-semibold text-slate-800">Amount</span>
            <span className="mt-2 flex h-12 items-center rounded-xl border border-slate-200 bg-white px-3 focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-100">
              <span className="text-sm font-bold text-slate-500">$</span>
              <input
                value={amount}
                onChange={(event) => onAmountChange(event.target.value)}
                disabled={isEvaluating}
                inputMode="decimal"
                placeholder="0.00"
                aria-label="Transfer amount"
                className="min-w-0 flex-1 border-0 bg-transparent px-3 text-right text-lg font-bold text-slate-950 outline-none disabled:cursor-not-allowed disabled:opacity-60"
              />
            </span>
            {amountValue > MANDATE_LIMIT && (
              <span className="mt-1 block text-xs text-red-600">
                Maximum amount is ${MANDATE_LIMIT.toLocaleString()}.
              </span>
            )}
          </label>

          <label className="block">
            <span className="text-sm font-semibold text-slate-800">Reference</span>
            <input
              value={note}
              onChange={(event) => onNoteChange(event.target.value)}
              disabled={isEvaluating}
              placeholder="What is this for?"
              maxLength={80}
              className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-50"
            />
          </label>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-slate-50 px-4 py-3">
          <div className="flex items-center gap-2 text-sm">
            <span
              className={`size-2 rounded-full ${isNewRecipient ? "bg-amber-500" : "bg-emerald-500"}`}
            />
            <span className="font-semibold text-slate-800">
              {isNewRecipient ? "New recipient" : "Previously paid recipient"}
            </span>
          </div>
          <span className="text-xs text-slate-500">
            Used by WAKALAH for risk classification
          </span>
        </div>

        <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">
            Demo script
          </p>
          <ul className="mt-1.5 space-y-1 text-xs text-slate-600">
            {DEMO_SCRIPT_HINTS.map((hint) => (
              <li key={hint}>• {hint}</li>
            ))}
          </ul>
        </div>

        {!isReady ? (
          <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-center text-xs leading-5 text-slate-500">
            {mandateStatus === "loading"
              ? "Setting up secure access…"
              : "Choose a phone number above to activate WAKALAH protection."}
          </p>
        ) : (
          <button
            type="submit"
            disabled={disabled}
            className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-blue-700 px-5 text-sm font-bold text-white shadow-sm transition hover:bg-blue-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isEvaluating ? (
              <>
                <span className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                WAKALAH is evaluating
              </>
            ) : (
              <>
                Simulate agent transfer <span aria-hidden>→</span>
              </>
            )}
          </button>
        )}
      </form>
    </section>
  );
}
