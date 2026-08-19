"use client";

import { useEffect, useRef, useState } from "react";

type PhoneDialogProps = {
  open: boolean;
  initialPhone: string;
  onClose: () => void;
  onSubmit: (phoneNumber: string) => void;
};

const phonePattern = /^\+[1-9][0-9]{4,14}$/;

export function PhoneDialog({
  open,
  initialPhone,
  onClose,
  onSubmit,
}: PhoneDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [phone, setPhone] = useState(initialPhone);
  const [error, setError] = useState("");

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      setPhone(initialPhone);
      setError("");
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [initialPhone, open]);

  function submit() {
    const normalized = phone.replace(/[\s()-]/g, "");
    if (!phonePattern.test(normalized)) {
      setError("Use international format, for example +99999991000.");
      return;
    }
    onSubmit(normalized);
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-3xl border-0 bg-transparent p-0 backdrop:bg-slate-950/55"
    >
      <div className="rounded-3xl bg-white p-6 shadow-2xl sm:p-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-700">
              Secure setup
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
              Add your phone number
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              WAKALAH uses it to create the agent&apos;s transaction mandate.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close phone number dialog"
            className="grid size-9 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-600 transition hover:bg-slate-200"
          >
            ×
          </button>
        </div>

        <label className="mt-6 block">
          <span className="text-sm font-semibold text-slate-800">Phone number</span>
          <input
            autoFocus
            type="tel"
            value={phone}
            onChange={(event) => {
              setPhone(event.target.value);
              setError("");
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") submit();
            }}
            placeholder="+99999991000"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "phone-error" : undefined}
            className={`mt-2 h-12 w-full rounded-xl border px-4 text-base text-slate-950 outline-none transition focus:ring-2 ${
              error
                ? "border-red-400 focus:border-red-500 focus:ring-red-100"
                : "border-slate-200 focus:border-blue-600 focus:ring-blue-100"
            }`}
          />
          {error && (
            <span id="phone-error" className="mt-2 block text-xs text-red-600">
              {error}
            </span>
          )}
        </label>

        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="h-11 flex-1 rounded-xl border border-slate-200 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={submit}
            className="h-11 flex-1 rounded-xl bg-blue-700 text-sm font-bold text-white transition hover:bg-blue-800"
          >
            Activate protection
          </button>
        </div>
      </div>
    </dialog>
  );
}
