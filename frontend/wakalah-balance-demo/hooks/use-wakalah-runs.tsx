
"use client";

import { useRef, useState } from "react";
import { useWakalahStream } from "@/hooks/use-wakalah-stream";
import {
  getEventTransactionId,
  isEvaluateResponse,
  normalizeDecision,
} from "@/lib/event-presentation";
import type {
  EvaluateResponse,
  EvaluationRun,
  MandateStatus,
  WsEvent,
} from "@/lib/types";

function asRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return value as Record<string, unknown>;
}

const MAX_RUNS = 25;

type UseWakalahRunsOptions = {
  resolveBeneficiaryName?: (beneficiaryId: string) => string;
  describeAction?: (ctx: {
    amount: number;
    beneficiaryName: string;
    beneficiaryId: string;
  }) => string;
};

export type ActiveBeat = {
  beatId: string;
  title: string;
  narration: string;
  expect: string;
  labels: string[];
} | null;

export type RevocationNotice = {
  kind: "revoked" | "mid_flight";
  mandateId: string | null;
  reason: string | null;
  verdictBefore: string | null;
  verdictNow: string | null;
} | null;

export function useWakalahRuns(options: UseWakalahRunsOptions = {}) {
  const { resolveBeneficiaryName, describeAction } = options;

  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [activeTransactionId, setActiveTransactionId] = useState<string | null>(
    null,
  );
  const [mandateStatus, setMandateStatus] = useState<MandateStatus>("idle");
  const [activeBeat, setActiveBeat] = useState<ActiveBeat>(null);
  const [revocation, setRevocation] = useState<RevocationNotice>(null);

  const pendingBeatTitleRef = useRef<string | null>(null);
  const seenRef = useRef(new Set<string>());

  const connectionStatus = useWakalahStream((event: WsEvent) => {
    if (event.type === "scenario.reset") {
      setActiveBeat(null);
      setRevocation(null);
      return;
    }

    if (event.type === "scenario.beat.started") {
      const payload = asRecord(event.payload);
      pendingBeatTitleRef.current =
        typeof payload.title === "string" ? payload.title : null;
      setActiveBeat({
        beatId: typeof payload.beatId === "string" ? payload.beatId : "",
        title: typeof payload.title === "string" ? payload.title : "",
        narration: typeof payload.narration === "string" ? payload.narration : "",
        expect: typeof payload.expect === "string" ? payload.expect : "",
        labels: Array.isArray(payload.labels)
          ? payload.labels.filter((l): l is string => typeof l === "string")
          : [],
      });
      return;
    }

    if (event.type === "mandate.updated") {
      const payload = asRecord(event.payload);
      setMandateStatus(payload.status === "active" ? "success" : "error");
    }

    if (event.type === "mandate.revoked") {
      const payload = asRecord(event.payload);
      setMandateStatus("idle");
      setRevocation({
        kind: "revoked",
        mandateId: typeof payload.mandateId === "string" ? payload.mandateId : null,
        reason: typeof payload.reason === "string" ? payload.reason : null,
        verdictBefore: null,
        verdictNow: null,
      });
    }

    if (event.type === "mandate.changed_mid_flight") {
      const payload = asRecord(event.payload);
      setRevocation({
        kind: "mid_flight",
        mandateId: null,
        reason: null,
        verdictBefore:
          typeof payload.verdictBefore === "string" ? payload.verdictBefore : null,
        verdictNow: typeof payload.verdictNow === "string" ? payload.verdictNow : null,
      });
    }

    const transactionId = getEventTransactionId(event);
    if (!transactionId) return;

    if (event.type === "transaction.started") {
      if (seenRef.current.has(transactionId)) {
        seenRef.current.delete(transactionId);

        setRuns((current) =>
          current.filter((run) => run.transactionId !== transactionId),
        );
      }

      seenRef.current.add(transactionId);

      const payload = asRecord(event.payload);
      const beneficiaryId =
        typeof payload.beneficiaryId === "string"
          ? payload.beneficiaryId
          : "unknown";

      const amount =
        typeof payload.amount === "number" ? payload.amount : 0;

      const beneficiaryName =
        resolveBeneficiaryName?.(beneficiaryId) ?? beneficiaryId;

      const run: EvaluationRun = {
        transactionId,
        action:
          pendingBeatTitleRef.current ??
          describeAction?.({
            amount,
            beneficiaryName,
            beneficiaryId,
          }) ??
          "Transfer request",
        phoneNumber:
          typeof payload.msisdn === "string" ? payload.msisdn : "",
        beneficiaryId,
        beneficiaryName,
        amount,
        isNewRecipient: Boolean(payload.beneficiaryIsNew),
        startedAt: event.ts,
        status: "running",
        events: [event],
        decision: null,
        error: null,
      };

      pendingBeatTitleRef.current = null;

      setRuns((current) => [run, ...current].slice(0, MAX_RUNS));
      setActiveTransactionId(transactionId);
      return;
    }

    if (!seenRef.current.has(transactionId)) return;

    setRuns((current) =>
      current.map((run) => {
        if (run.transactionId !== transactionId) return run;

        const events = [...run.events, event];

        if (
          event.type === "decision.final" &&
          isEvaluateResponse(event.payload)
        ) {
          const decision = event.payload as EvaluateResponse;

          setActiveTransactionId((currentId) =>
            currentId === transactionId ? null : currentId,
          );
          return {
            ...run,
            events,
            status: "completed" as const,
            decision: {
              ...decision,
              decision: normalizeDecision(decision.decision),
            },
          };
        }

        return {
          ...run,
          events, 
        };
      }),
    );
   
  });

  function markRunFailed(transactionId: string, message: string) {
    setRuns((current) =>
      current.map((run) =>
        run.transactionId === transactionId && run.status === "running"
          ? {
              ...run,
              status: "failed" as const,
              error: message,
            }
          : run,
      ),
    );

    setActiveTransactionId((currentId) =>
      currentId === transactionId ? null : currentId,
    );
  }

  return {
    runs,
    activeTransactionId,
    connectionStatus,
    mandateStatus,
    setMandateStatus,
    markRunFailed,
    activeBeat,
    revocation,
  };
}