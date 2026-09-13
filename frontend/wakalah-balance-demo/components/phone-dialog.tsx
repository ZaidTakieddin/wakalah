"use client";

import { useEffect, useRef, useState } from "react";

type PhoneDialogProps = {
  open: boolean;
  initialPhone: string;
  onClose: () => void;
  onSubmit: (phoneNumber: string) => void;
};

type Persona = {
  value: string;
  label: string;
  description: string;
};

// The Nokia sandbox roster (docs/02 §5.6): fixed behaviour per number, so the
// demo can stage every story — clean approval, takeover, outage, error path.
const PERSONAS: Persona[] = [
  {
    value: "+99999991001",
    label: "Amina — clean user",
    description: "Every network check passes. Transfers get approved.",
  },
  {
    value: "+99999991000",
    label: "Compromised account",
    description:
      "SIM swapped, new device, calls forwarded, number recycled. Expect DENY.",
  },
  {
    value: "+99999990503",
    label: "Outage simulator",
    description:
      "The network always fails (representative of the 0500–0504 family). Expect CHALLENGE — never approval.",
  },
  {
    value: "+99999990404",
    label: "Error simulator",
    description:
      "Every API answers 404 (representative of the 0400/0404/0422 family). Tests error handling.",
  },
];

const DEFAULT_PERSONA = PERSONAS[0].value;

function resolveInitial(initialPhone: string): string {
  return PERSONAS.some((persona) => persona.value === initialPhone)
    ? initialPhone
    : DEFAULT_PERSONA;
}

export function PhoneDialog({
  open,
  initialPhone,
  onClose,
  onSubmit,
}: PhoneDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [phone, setPhone] = useState(() => resolveInitial(initialPhone));

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      setPhone(resolveInitial(initialPhone));
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [initialPhone, open]);

  const selected = PERSONAS.find((persona) => persona.value === phone) ?? PERSONAS[0];

  function submit() {
    onSubmit(phone);
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
          <select
            autoFocus
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            aria-describedby="persona-description"
            className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-base text-slate-950 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
          >
            {PERSONAS.map((persona) => (
              <option key={persona.value} value={persona.value}>
                {persona.value} — {persona.label}
              </option>
            ))}
          </select>
          <span
            id="persona-description"
            className="mt-2 block rounded-xl bg-slate-50 px-4 py-2.5 text-xs leading-5 text-slate-600"
          >
            {selected.description}
          </span>
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
