import type { TransferRecord } from "@/lib/types";

export const DEMO_AGENT = {
  id: "agent_rasheed",
  name: "Rasheed AI",
  keyFingerprint: "fp_rasheed_ed25519",
} as const;

export const MANDATE_LIMIT = 2_000;

export const INITIAL_TRANSFERS: TransferRecord[] = [
  {
    id: "transfer_001",
    transactionId: "tx_history_001",
    beneficiaryId: "hessa-al-mansoori",
    beneficiaryName: "Hessa Al-Mansoori",
    amount: 450,
    currency: "USD",
    status: "completed",
    isNewRecipient: false,
    requestedAt: "2026-08-17T09:20:00+03:00",
  },
  {
    id: "transfer_002",
    transactionId: "tx_history_002",
    beneficiaryId: "doha-properties",
    beneficiaryName: "Doha Properties",
    amount: 1_850,
    currency: "USD",
    status: "completed",
    isNewRecipient: false,
    requestedAt: "2026-08-14T18:45:00+03:00",
  },
  {
    id: "transfer_003",
    transactionId: "tx_history_003",
    beneficiaryId: "lina-pharmacy",
    beneficiaryName: "Lina Pharmacy",
    amount: 125,
    currency: "USD",
    status: "completed",
    isNewRecipient: false,
    requestedAt: "2026-07-17T09:18:00+03:00",
  },
];

export const RECIPIENT_NAMES = INITIAL_TRANSFERS.map(
  (transfer) => transfer.beneficiaryName,
);

export function recipientIdFromName(name: string) {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export const AUTHORIZED_BENEFICIARY_IDS = [
  "hessa-al-mansoori",
  "doha-properties",
  "lina-pharmacy",
  // Permitted but never paid: typing this name stages the step-up path
  // (first material payment to a new beneficiary always challenges).
  "omar-cafe",
];

/** Suggested in the recipient dropdown, but intentionally NOT a "known"
 *  recipient — picking it stages the step-up path. */
export const NEW_RECIPIENT_SUGGESTION = "Omar Cafe";

/** What each home-page transfer demonstrates. Kept next to the data so the
 *  presenter never has to guess. */
export const DEMO_SCRIPT_HINTS = [
  "500 to Hessa Al-Mansoori → ALLOW",
  "1,500 to Omar Cafe (new) → CHALLENGE",
  "5,000 anywhere → DENY (over the limit)",
] as const;

export type Persona = {
  value: string;
  short: string;
  label: string;
  description: string;
};

// The Nokia sandbox roster (docs/02 §5.6): fixed behaviour per number, so the
// demo can stage every story — clean approval, takeover, outage, error path.
export const PERSONAS: Persona[] = [
  {
    value: "+99999991001",
    short: "Amina",
    label: "Amina — clean user",
    description: "Every network check passes. Transfers get approved.",
  },
  {
    value: "+99999991000",
    short: "Compromised",
    label: "Compromised account",
    description:
      "SIM swapped, new device, calls forwarded, number recycled. Expect DENY.",
  },
  {
    value: "+99999990503",
    short: "Outage",
    label: "Outage simulator",
    description:
      "The network always fails (representative of the 0500–0504 family). Expect CHALLENGE — never approval.",
  },
  {
    value: "+99999990404",
    short: "Error",
    label: "Error simulator",
    description:
      "Every API answers 404 (representative of the 0400/0404/0422 family). Tests error handling.",
  },
];

export const DEFAULT_PERSONA = PERSONAS[0].value;
