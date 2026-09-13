"use client";

import { useEffect, useMemo, useState } from "react";
import { createMandate, evaluateTransaction } from "@/actions/wakalah";
import { AppHeader } from "@/components/dashboard/app-header";
import { TransferForm } from "@/components/dashboard/transfer-form";
import { TransferHistory } from "@/components/dashboard/transfer-history";
import { TransferLivePanel } from "@/components/wakalah/transfer-live-panel";
import {
  DEFAULT_PERSONA,
  INITIAL_TRANSFERS,
  RECIPIENT_NAMES,
  recipientIdFromName,
} from "@/lib/demo-data";
import type { MandateResponse, TransferRecord } from "@/lib/types";
import { revokeActiveMandates } from "@/lib/revoke-active-mandates";
import { useWakalahRuns } from "@/hooks/use-wakalah-runs";

export default function Home() {
  const [recipientName, setRecipientName] = useState(RECIPIENT_NAMES[0]);
  const [amount, setAmount] = useState("500");
  const [note, setNote] = useState("Monthly support");

  const [phoneNumber, setPhoneNumber] = useState("");
  const [mandate, setMandate] = useState<MandateResponse | null>(null);
  const [mandateError, setMandateError] = useState<string | null>(null);

  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [pendingTransactionId, setPendingTransactionId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [lastAutoExpanded, setLastAutoExpanded] = useState<string | null>(null);

  const normalizedRecipientName = recipientName.trim();
  const isNewRecipient = !RECIPIENT_NAMES.some(
    (name) => name.toLocaleLowerCase() === normalizedRecipientName.toLocaleLowerCase(),
  );

  // Home knows real recipient names; scenario runs don't need this, so it's
  // an option the hook accepts rather than something it assumes.
  const nameByBeneficiaryId = useMemo(
    () => new Map(RECIPIENT_NAMES.map((name) => [recipientIdFromName(name), name])),
    [],
  );
  const resolveBeneficiaryName = (beneficiaryId: string) =>
    nameByBeneficiaryId.get(beneficiaryId) ?? beneficiaryId;

  const {
    runs,
    activeTransactionId,
    connectionStatus,
    mandateStatus,
    setMandateStatus,
    markRunFailed,
  } = useWakalahRuns({
    resolveBeneficiaryName,
    describeAction: ({ amount, beneficiaryName }) =>
      `Transfer ${amount.toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })} to ${beneficiaryName}`,
  });

  // pendingTransactionId covers the gap between clicking submit and the WS
  // confirming the run started — without it the button could double-fire.
  const isEvaluating = pendingTransactionId !== null || activeTransactionId !== null;

  // Auto-expand the active run. Adjusted during render (not in an effect) so
  // a manual collapse while the run is active is respected afterwards.
  if (activeTransactionId !== lastAutoExpanded) {
    setLastAutoExpanded(activeTransactionId);
    if (activeTransactionId) setExpandedRunId(activeTransactionId);
  }

  // Finished runs are derived into history during render — no mirror effect,
  // no ref bookkeeping, nothing to run twice.
  const transfers: TransferRecord[] = useMemo(
    () => [
      ...runs
        .filter((run) => run.status !== "running")
        .map((run) => ({
          id: `transfer_${run.transactionId}`,
          transactionId: run.transactionId,
          beneficiaryId: run.beneficiaryId,
          beneficiaryName: run.beneficiaryName,
          amount: run.amount,
          currency: "USD" as const,
          status:
            run.status === "failed"
              ? ("failed" as const)
              : run.decision?.decision === "allow"
                ? ("completed" as const)
                : run.decision?.decision === "deny"
                  ? ("denied" as const)
                  : ("challenge" as const),
          isNewRecipient: run.isNewRecipient,
          requestedAt: run.startedAt,
        })),
      ...INITIAL_TRANSFERS,
    ],
    [runs],
  );

  useEffect(() => {
    void revokeActiveMandates("page_load_reset");
  }, []);

  async function activatePhone(nextPhoneNumber: string) {
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
        error instanceof Error ? error.message : "WAKALAH could not prepare this account.",
      );
    }
  }

  async function submitTransfer() {
    if (!mandate || isEvaluating) return;

    const transferAmount = Number(amount);
    if (!Number.isFinite(transferAmount) || transferAmount <= 0) return;

    const beneficiaryName = normalizedRecipientName;
    if (!beneficiaryName) return;

    const transactionId = `tx_${crypto.randomUUID()}`;
    const beneficiaryId = recipientIdFromName(beneficiaryName);

    setSubmitError(null);
    setPendingTransactionId(transactionId);
    setExpandedRunId(transactionId);

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
      // The live stream (transaction.started -> ... -> decision.final) takes
      // it from here; `runs` and the history table update via the effects above.
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "WAKALAH could not evaluate this transfer.";
      markRunFailed(transactionId, message);
      setSubmitError(message);
    } finally {
      setPendingTransactionId(null);
    }
  }

  return (
    <main className="min-h-screen bg-[#f5f7fb] text-slate-950">
      <AppHeader />

      <div className="mx-auto grid max-w-385 gap-5 p-4 sm:p-5 lg:grid-cols-[minmax(0,1fr)_460px]">
        <div className="min-w-0 space-y-5">
          <TransferForm
            recipientName={recipientName}
            recipientOptions={RECIPIENT_NAMES}
            amount={amount}
            note={note}
            mandateStatus={mandateStatus}
            isEvaluating={isEvaluating}
            isNewRecipient={isNewRecipient}
            phoneNumber={phoneNumber}
            onRecipientChange={setRecipientName}
            onAmountChange={setAmount}
            onNoteChange={setNote}
            onSubmit={() => void submitTransfer()}
            onPhoneSelect={(nextPhoneNumber) => void activatePhone(nextPhoneNumber)}
          />
          {submitError && (
            <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {submitError}
            </p>
          )}

          <TransferHistory transfers={transfers} />
        </div>

        <TransferLivePanel
          phoneNumber={phoneNumber}
          mandateStatus={mandateStatus}
          mandateError={mandateError}
          connectionStatus={connectionStatus}
          runs={runs}
          expandedRunId={expandedRunId}
          isEvaluating={isEvaluating}
          onSetPhone={() => void activatePhone(DEFAULT_PERSONA)}
          onRetryMandate={() => void activatePhone(phoneNumber)}
          onToggleRun={(transactionId) =>
            setExpandedRunId((current) => (current === transactionId ? null : transactionId))
          }
        />
      </div>
    </main>
  );
}