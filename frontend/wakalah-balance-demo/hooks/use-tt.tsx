"use client";

import { useRef, useState } from "react";
import { useWakalahStream } from "@/hooks/use-wakalah-stream";
import {
  isEvaluateResponse,
  normalizeDecision,
} from "@/lib/event-presentation";
import type {
  EvaluateResponse,
  EvaluationRun,
  MandateStatus,
  WsEvent,
} from "@/lib/types";

function asRecord(value: unknown): Record<string, any> {
  return value && typeof value === "object" ? (value as Record<string, any>) : {};
}

const MAX_RUNS = 25;

// Used as the initial `action` label when a beat carries no `title`. Kept as
// a named sentinel (rather than an inline magic string) so the
// `transaction.started` handler can tell "no real title yet" apart from a
// legitimately generic-sounding title.
const UNTITLED_BEAT_ACTION = "Scenario step";

type UseWakalahRunsOptions = {
  resolveBeneficiaryName?: (beneficiaryId: string) => string;
  describeAction?: (ctx: {
    amount: number;
    beneficiaryName: string;
    beneficiaryId: string;
  }) => string;
};

export function useWakalahRuns(options: UseWakalahRunsOptions = {}) {
  const { resolveBeneficiaryName, describeAction } = options;

  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [activeBeatId, setActiveBeatId] = useState<string | null>(null);
  const [mandateStatus, setMandateStatus] = useState<MandateStatus>("idle");

  // The beat currently "open" (between scenario.beat.started and
  // scenario.beat.finished). Every event that isn't itself a beat boundary
  // gets filed against whichever beat is open right now — this is what lets
  // id-less events like `nac.call` still land in the right run.
  const activeBeatIdRef = useRef<string | null>(null);
  const seenBeatIdsRef = useRef(new Set<string>());

  const connectionStatus = useWakalahStream((event: WsEvent) => {
    if (event.type === "scenario.reset") {
      activeBeatIdRef.current = null;
      seenBeatIdsRef.current = new Set();
      setActiveBeatId(null);
      setRuns([]);
      return;
    }

    if (event.type === "scenario.beat.started") {
      const payload = asRecord(event.payload);
      const beatId = typeof payload.id === "string" ? payload.id : `beat-${event.ts}`;

      // If a previous beat never got a scenario.beat.finished (interrupted
      // demo, dropped connection, whatever), don't leave it stuck spinning.
      const staleBeatId = activeBeatIdRef.current;
      if (staleBeatId && staleBeatId !== beatId) {
        setRuns((current) =>
          current.map((run) =>
            run.id === staleBeatId && run.status === "running"
              ? { ...run, status: "failed" as const, error: "Interrupted by next scenario beat" }
              : run,
          ),
        );
      }

      // Defensive: a replayed/duplicate beat id shouldn't create a second row.
      if (seenBeatIdsRef.current.has(beatId)) {
        seenBeatIdsRef.current.delete(beatId);
        setRuns((current) => current.filter((run) => run.id !== beatId));
      }
      seenBeatIdsRef.current.add(beatId);

      const title = typeof payload.title === "string" ? payload.title : null;

      const run: EvaluationRun = {
        id: beatId,
        transactionId: null, // filled in later if a transaction.started arrives
        action: title ?? UNTITLED_BEAT_ACTION,
        phoneNumber: "",
        beneficiaryId: "",
        beneficiaryName: "",
        amount: 0,
        isNewRecipient: false,
        startedAt: event.ts,
        status: "running",
        events: [event],
        decision: null,
        error: null,
      };

      activeBeatIdRef.current = beatId;
      setActiveBeatId(beatId);
      setRuns((current) => [run, ...current].slice(0, MAX_RUNS));
      return;
    }

    // Global mandate-status widget: updated regardless of whether there's an
    // open beat to also log the raw event against.
    if (event.type === "mandate.updated") {
      const payload = asRecord(event.payload);
      setMandateStatus(payload.status === "active" ? "success" : "error");
    } else if (event.type === "mandate.revoked") {
      setMandateStatus("idle");
    }

    // scenario.beat.finished names its target explicitly via `beatId`; every
    // other mid-beat event (transaction.started, agent.trace, nac.call,
    // decision.final, mandate.*, mandate.changed_mid_flight, ...) is filed
    // against whatever beat is currently open.
    let targetBeatId = activeBeatIdRef.current;
    if (event.type === "scenario.beat.finished") {
      const payload = asRecord(event.payload);
      if (typeof payload.beatId === "string") targetBeatId = payload.beatId;
    }

    if (!targetBeatId || !seenBeatIdsRef.current.has(targetBeatId)) return;

    setRuns((current) =>
      current.map((run) => {
        if (run.id !== targetBeatId) return run;

        const events = [...run.events, event];

        if (event.type === "transaction.started") {
          const payload = asRecord(event.payload);
          const beneficiaryId =
            typeof payload.beneficiaryId === "string" ? payload.beneficiaryId : "unknown";
          const amount =
            typeof payload.amount?.value === "number" ? payload.amount.value : 0;
          const beneficiaryName = resolveBeneficiaryName?.(beneficiaryId) ?? beneficiaryId;

          return {
            ...run,
            events,
            transactionId:
              typeof payload.transactionId === "string" ? payload.transactionId : run.transactionId,
            phoneNumber: typeof payload.principal === "string" ? payload.principal : run.phoneNumber,
            beneficiaryId,
            beneficiaryName,
            amount,
            isNewRecipient: Boolean(payload.beneficiaryIsNew),
            // Beat title (set at beat.started) always wins over a generated
            // description; only fall back to describeAction if there was no
            // real title.
            action:
              run.action === UNTITLED_BEAT_ACTION
                ? describeAction?.({ amount, beneficiaryName, beneficiaryId }) ?? run.action
                : run.action,
          };
        }

        if (event.type === "decision.final" && isEvaluateResponse(event.payload)) {
          const decision = event.payload as EvaluateResponse;
          return {
            ...run,
            events,
            decision: {
              ...decision,
              decision: normalizeDecision(decision.decision),
            },
          };
        }

        if (event.type === "scenario.beat.finished") {
          const payload = asRecord(event.payload);
          activeBeatIdRef.current = null;
          setActiveBeatId((current) => (current === targetBeatId ? null : current));
          return {
            ...run,
            events,
            status: payload.ok === false ? ("failed" as const) : ("completed" as const),
            error:
              payload.ok === false && typeof payload.summary === "string"
                ? payload.summary
                : run.error,
          };
        }

        // agent.trace, nac.call, mandate.updated, mandate.revoked,
        // mandate.changed_mid_flight, and anything else: just log it into
        // the beat's timeline as-is.
        return { ...run, events };
      }),
    );
  });

  function markRunFailed(beatId: string, message: string) {
    setRuns((current) =>
      current.map((run) =>
        run.id === beatId && run.status === "running"
          ? { ...run, status: "failed" as const, error: message }
          : run,
      ),
    );
    setActiveBeatId((current) => (current === beatId ? null : current));
    if (activeBeatIdRef.current === beatId) activeBeatIdRef.current = null;
  }

  return {
    runs,
    activeBeatId,
    connectionStatus,
    mandateStatus,
    setMandateStatus,
    markRunFailed,
  };
}