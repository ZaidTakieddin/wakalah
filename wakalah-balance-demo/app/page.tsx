"use client";

import { useRef, useState } from "react";
import { createMandate, evaluateTransaction } from "@/actions/wakalah";
import { AppHeader } from "@/components/dashboard/app-header";
import { TransferForm } from "@/components/dashboard/transfer-form";
import { TransferHistory } from "@/components/dashboard/transfer-history";
import { PhoneDialog } from "@/components/phone-dialog";
import { LivePanel } from "@/components/wakalah/live-panel";
import { useWakalahStream } from "@/hooks/use-wakalah-stream";
import {
  getEventTransactionId,
  isEvaluateResponse,
  normalizeDecision,
} from "@/lib/event-presentation";
import {
  INITIAL_TRANSFERS,
  RECIPIENT_NAMES,
  recipientIdFromName,
} from "@/lib/demo-data";
import type {
  Decision,
  EvaluateResponse,
  EvaluationRun,
  MandateResponse,
  MandateStatus,
  RiskTier,
  TransferRecord,
  WsEvent,
} from "@/lib/types";

type RunContext = {
  transactionId: string;
  beneficiaryId: string;
  beneficiaryName: string;
  amount: number;
  isNewRecipient: boolean;
  requestedAt: string;
};

function normalizeRiskTier(value: unknown): RiskTier {
  const tier = String(value ?? "medium").toLowerCase();
  if (tier === "low" || tier === "high") return tier;
  return "medium";
}

function normalizeEvaluateResponse(
  value: EvaluateResponse | Record<string, unknown>,
  transactionId: string,
): EvaluateResponse {
  const response = value as unknown as Record<string, unknown>;
  const proposal = response.agentProposal;

  return {
    transactionId:
      typeof response.transactionId === "string"
        ? response.transactionId
        : transactionId,
    decision: normalizeDecision(String(response.decision ?? "challenge")),
    riskTier: normalizeRiskTier(response.riskTier),
    reasonCodes: Array.isArray(response.reasonCodes)
      ? response.reasonCodes.filter(
          (reason): reason is string => typeof reason === "string",
        )
      : [],
    rationale:
      typeof response.rationale === "string" ? response.rationale : "",
    agentProposal:
      typeof proposal === "string" ? normalizeDecision(proposal) : null,
    policyOverrodeAgent: response.policyOverrodeAgent === true,
    latencyMs:
      typeof response.latencyMs === "number" ? response.latencyMs : null,
  };
}

export default function Home() {
  const [transfers, setTransfers] =
    useState<TransferRecord[]>(INITIAL_TRANSFERS);
  const [recipientName, setRecipientName] = useState(RECIPIENT_NAMES[0]);
  const [amount, setAmount] = useState("500");
  const [note, setNote] = useState("Monthly support");

  const [phoneDialogOpen, setPhoneDialogOpen] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [mandate, setMandate] = useState<MandateResponse | null>(null);
  const [mandateStatus, setMandateStatus] =
    useState<MandateStatus>("idle");
  const [mandateError, setMandateError] = useState<string | null>(null);

  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [activeTransactionId, setActiveTransactionId] = useState<string | null>(
    null,
  );
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  const runContextsRef = useRef(new Map<string, RunContext>());
  const completedRunsRef = useRef(new Set<string>());

  const normalizedRecipientName = recipientName.trim();
  const isNewRecipient = !RECIPIENT_NAMES.some(
    (name) =>
      name.toLocaleLowerCase() === normalizedRecipientName.toLocaleLowerCase(),
  );
  const isEvaluating = activeTransactionId !== null;

  const connectionStatus = useWakalahStream((event) => {
    const transactionId = getEventTransactionId(event) ?? activeTransactionId;
    if (!transactionId || !runContextsRef.current.has(transactionId)) return;

    appendEvent(transactionId, event);

    if (event.type === "decision.final") {
      completeRun(
        transactionId,
        normalizeEvaluateResponse(
          event.payload as Record<string, unknown>,
          transactionId,
        ),
      );
    }
  });

  function appendEvent(transactionId: string, event: WsEvent) {
    setRuns((current) =>
      current.map((run) => {
        if (run.transactionId !== transactionId) return run;
        const duplicate = run.events.some(
          (existing) =>
            existing.type === event.type && existing.ts === event.ts,
        );
        return duplicate ? run : { ...run, events: [...run.events, event] };
      }),
    );
  }

  function completeRun(transactionId: string, decision: EvaluateResponse) {
    if (completedRunsRef.current.has(transactionId)) return;

    const context = runContextsRef.current.get(transactionId);
    if (!context) return;

    completedRunsRef.current.add(transactionId);
    const normalizedDecision: Decision = normalizeDecision(decision.decision);
    const normalizedResponse = { ...decision, decision: normalizedDecision };

    setRuns((current) =>
      current.map((run) =>
        run.transactionId === transactionId
          ? {
              ...run,
              status: "completed",
              decision: normalizedResponse,
              error: null,
            }
          : run,
      ),
    );

    const transferStatus: TransferRecord["status"] =
      normalizedDecision === "allow"
        ? "completed"
        : normalizedDecision === "deny"
          ? "denied"
          : "challenge";

    setTransfers((current) =>
      [
        {
          id: `transfer_${transactionId}`,
          transactionId,
          beneficiaryId: context.beneficiaryId,
          beneficiaryName: context.beneficiaryName,
          amount: context.amount,
          currency: "USD" as const,
          status: transferStatus,
          isNewRecipient: context.isNewRecipient,
          requestedAt: context.requestedAt,
        },
        ...current,
      ]
    );

    setActiveTransactionId((current) =>
      current === transactionId ? null : current,
    );
  }

  function failRun(transactionId: string, message: string) {
    if (completedRunsRef.current.has(transactionId)) return;
    const context = runContextsRef.current.get(transactionId);
    if (!context) return;

    completedRunsRef.current.add(transactionId);
    setRuns((current) =>
      current.map((run) =>
        run.transactionId === transactionId
          ? { ...run, status: "failed", error: message }
          : run,
      ),
    );
    setTransfers((current) =>
      [
        {
          id: `transfer_${transactionId}`,
          transactionId,
          beneficiaryId: context.beneficiaryId,
          beneficiaryName: context.beneficiaryName,
          amount: context.amount,
          currency: "USD" as const,
          status: "failed" as const,
          isNewRecipient: context.isNewRecipient,
          requestedAt: context.requestedAt,
        },
        ...current,
      ]
    );
    setActiveTransactionId((current) =>
      current === transactionId ? null : current,
    );
  }

  async function activatePhone(nextPhoneNumber: string) {
    setPhoneDialogOpen(false);
    setPhoneNumber(nextPhoneNumber);
    setMandate(null);
    setMandateStatus("loading");
    setMandateError(null);

    try {
      const result = await createMandate(nextPhoneNumber);
      if (!result.ok) throw new Error(result.error);
      const response = result.data;
      if (response.status !== "active") {
        throw new Error("The transaction authorization is not active.");
      }
      setMandate(response);
      setMandateStatus("success");
    } catch (error) {
      setMandateStatus("error");
      setMandateError(
        error instanceof Error
          ? error.message
          : "WAKALAH could not prepare this account.",
      );
    }
  }

  async function submitTransfer() {
    if (!mandate || activeTransactionId) return;

    const transferAmount = Number(amount);
    if (!Number.isFinite(transferAmount) || transferAmount <= 0) return;

    const transactionId = `tx_${crypto.randomUUID()}`;
    const requestedAt = new Date().toISOString();
    const beneficiaryName = normalizedRecipientName;
    if (!beneficiaryName) return;

    const beneficiaryId = recipientIdFromName(beneficiaryName);
    const action = `Transfer ${transferAmount.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} to ${beneficiaryName}`;

    const context: RunContext = {
      transactionId,
      beneficiaryId,
      beneficiaryName,
      amount: transferAmount,
      isNewRecipient,
      requestedAt,
    };
    runContextsRef.current.set(transactionId, context);

    const run: EvaluationRun = {
      transactionId,
      action,
      phoneNumber,
      beneficiaryId,
      beneficiaryName,
      amount: transferAmount,
      isNewRecipient,
      startedAt: requestedAt,
      status: "running",
      events: [],
      decision: null,
      error: null,
    };

    setRuns((current) => [run, ...current]);
    setExpandedRunId(transactionId);
    setActiveTransactionId(transactionId);

    try {
      const result = await evaluateTransaction({
        transactionId,
        mandateId: mandate.mandateId,
        amount: transferAmount,
        currency: "USD",
        beneficiaryId,
        beneficiaryIsNew: isNewRecipient,
      });
      if (!result.ok) throw new Error(result.error);
      const response = result.data;

      if (isEvaluateResponse(response)) {
        completeRun(
          transactionId,
          normalizeEvaluateResponse(response, transactionId),
        );
      }
    } catch (error) {
      failRun(
        transactionId,
        error instanceof Error
          ? error.message
          : "WAKALAH could not evaluate this transfer.",
      );
    }
  }

  return (
    <main className="min-h-screen bg-[#f5f7fb] text-slate-950">
      <AppHeader />

      <div className="mx-auto grid max-w-385 gap-5 p-4 sm:p-5 xl:grid-cols-[minmax(0,1fr)_460px]">
        <div className="min-w-0 space-y-5">
          <TransferForm
            recipientName={recipientName}
            recipientOptions={RECIPIENT_NAMES}
            amount={amount}
            note={note}
            mandateStatus={mandateStatus}
            isEvaluating={isEvaluating}
            isNewRecipient={isNewRecipient}
            onRecipientChange={setRecipientName}
            onAmountChange={setAmount}
            onNoteChange={setNote}
            onSubmit={() => void submitTransfer()}
            onSetPhone={() => setPhoneDialogOpen(true)}
          />

          <TransferHistory transfers={transfers} />
        </div>

        <LivePanel
          phoneNumber={phoneNumber}
          mandateStatus={mandateStatus}
          mandateError={mandateError}
          connectionStatus={connectionStatus}
          runs={runs}
          expandedRunId={expandedRunId}
          isEvaluating={isEvaluating}
          onSetPhone={() => setPhoneDialogOpen(true)}
          onRetryMandate={() => void activatePhone(phoneNumber)}
          onToggleRun={(transactionId) =>
            setExpandedRunId((current) =>
              current === transactionId ? null : transactionId,
            )
          }
        />
      </div>

      <PhoneDialog
        open={phoneDialogOpen}
        initialPhone={phoneNumber}
        onClose={() => setPhoneDialogOpen(false)}
        onSubmit={(nextPhoneNumber) => void activatePhone(nextPhoneNumber)}
      />
    </main>
  );
}
