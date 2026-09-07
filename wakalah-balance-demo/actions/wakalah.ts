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

const getApiBase =
  process.env.WAKALAH_API_BASE ?? "http://127.0.0.1:8000";

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
    const response = await fetch(`${getApiBase}/v1/mandates`, {
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


    const response = await fetch(`${getApiBase}/v1/transactions/evaluate`, {
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
