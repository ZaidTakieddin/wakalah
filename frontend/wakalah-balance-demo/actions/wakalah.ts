"use server";

import {
  AUTHORIZED_BENEFICIARY_IDS,
  DEMO_AGENT,
  MANDATE_LIMIT,
} from "@/lib/demo-data";
import type {
  EvaluateResponse,
  EvaluateTransactionInput,
  MandateResponse,
} from "@/lib/types";

const API_BASE =  process.env.WAKALAH_API_BASE;

async function getErrorMessage(response: Response, fallback: string) {
  try {
    const body = (await response.json()) as { detail?: string; message?: string };
    return body.detail ?? body.message ?? fallback;
  } catch {
    return fallback;
  }
}

export async function createMandate(
  phoneNumber: string,
): Promise<
  | { ok: true; data: MandateResponse }
  | { ok: false; error: string }
> {
  try {
    const response = await fetch(`${API_BASE}/v1/mandates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        principalMsisdn: phoneNumber,
        agentId: DEMO_AGENT.id,
        agentKeyFingerprint: DEMO_AGENT.keyFingerprint,
        amountLimit: MANDATE_LIMIT,
        currency: "USD",
        beneficiaryIds: AUTHORIZED_BENEFICIARY_IDS,
      }),
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        ok: false,
        error: await getErrorMessage(
          response,
          "WAKALAH could not prepare this account. Please try again.",
        ),
      };
    }
    const data = await response.json() as MandateResponse;
console.log(data)
    return { ok: true, data };
  } catch (error) {
    console.error("Failed to create mandate:", error);
    return {
      ok: false,
      error: "WAKALAH is temporarily unavailable. Check the connection and try again.",
    };
  }
}

export async function evaluateTransaction(
  input: EvaluateTransactionInput,
): Promise<
  | { ok: true; data: EvaluateResponse | Record<string, unknown> }
  | { ok: false; error: string }
> {
  try {


    const response = await fetch(`${API_BASE}/v1/transactions/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transactionId: input.transactionId,
        mandateId: input.mandateId,
        amount: {
          value: input.amount,
          currency: input.currency,
        },
        beneficiaryId: input.beneficiaryId,
        beneficiaryIsNew: input.beneficiaryIsNew,
      }),
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        ok: false,
        error: await getErrorMessage(
          response,
          "WAKALAH could not review this transfer. Please try again.",
        ),
      };
    }

    return {
      ok: true,
      data: (await response.json()) as EvaluateResponse | Record<string, unknown>,
    };
  } catch {
    return {
      ok: false,
      error: "WAKALAH is temporarily unavailable. The transfer was not sent.",
    };
  }
}

export async function listMandates() {
  try {
    const res = await fetch(`${API_BASE}/v1/mandates`); // adjust API_BASE to your existing constant/import
    if (!res.ok) throw new Error(await res.text());
    const data = (await res.json()) as MandateResponse[];
    return { ok: true as const, data };
  } catch (error) {
    return {
      ok: false as const,
      error: error instanceof Error ? error.message : "Failed to list mandates.",
    };
  }
}

export async function revokeMandate(mandateId: string, reason: string) {
  try {
    const res = await fetch(
      `${API_BASE}/v1/mandates/${mandateId}/revoke?reason=${encodeURIComponent(reason)}`,
      { method: "POST" },
    );
    if (!res.ok) throw new Error(await res.text());
    return { ok: true as const, data: await res.json() };
  } catch (error) {
    return {
      ok: false as const,
      error: error instanceof Error ? error.message : "Failed to revoke mandate.",
    };
  }
}
