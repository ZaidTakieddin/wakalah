"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, Loader2, Play, PlayCircle, RotateCcw } from "lucide-react";
import {
  getScenario,
  resetScenario,
  runAllScenarioBeats,
  runScenarioBeat,
  type Scenario,
} from "@/actions/scenario";
import { revokeActiveMandates } from "@/lib/revoke-active-mandates";

type Busy = "beat" | "all" | "reset" | null;

export function ScenarioRunner() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<Busy>(null);
  const [busyBeatId, setBusyBeatId] = useState<string | null>(null);
  const [expandedBeat, setExpandedBeat] = useState<string | null>(null);
  const initRef = useRef(false);

  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;

    (async () => {
      try {
        await revokeActiveMandates("page_load_reset");
        setScenario(await getScenario());
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const isBusy = busy !== null;
  const beats = scenario?.beats ?? [];
  const completedBeats = beats.filter((beat) => beat.done).length;

  // Every action below: fire the mutation, THEN fetch fresh scenario state,
  // THEN clear busy. Not before — the action's own return value may reflect
  // state before the backend has fully settled (decisions stream in async
  // over the socket), so we don't trust it for what to render.
  async function runBeat(beatId: string) {
    if (isBusy) return;
    setBusy("beat");
    setBusyBeatId(beatId);
    try {
      await runScenarioBeat(beatId);
      setScenario(await getScenario());
    } finally {
      setBusy(null);
      setBusyBeatId(null);
    }
  }

  async function runAll() {
    if (isBusy) return;
    setBusy("all");
    try {
      await runAllScenarioBeats();
      setScenario(await getScenario());
    } finally {
      setBusy(null);
    }
  }

  async function reset() {
    if (isBusy) return;
    setBusy("reset");
    try {
      await revokeActiveMandates("scenario_reset");
      await resetScenario();
      setScenario(await getScenario());
      setExpandedBeat(null);
    } finally {
      setBusy(null);
    }
  }

  if (loading) {
    return (
      <section className="rounded-2xl border bg-card p-6">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading scenario...
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="rounded-2xl border bg-card p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <PlayCircle className="h-5 w-5" />
              <h2 className="text-lg font-semibold">Scenario Runner</h2>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              Run the WAKALAH trust scenarios individually or as a full sequence.
            </p>
            <div className="mt-3 text-xs text-muted-foreground">
              {completedBeats} of {beats.length} completed
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void reset()}
              disabled={isBusy}
              className="inline-flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy === "reset" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
              {busy === "reset" ? "Resetting..." : "Reset"}
            </button>

            <button
              type="button"
              onClick={() => void runAll()}
              disabled={isBusy}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy === "all" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              {busy === "all" ? "Running..." : "Run all"}
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {beats.map((beat, index) => {
          const isRunning = busyBeatId === beat.id;
          const isExpanded = expandedBeat === beat.id;

          return (
            <article key={beat.id} className="rounded-2xl border bg-card p-4">
              <div className="flex gap-4">
                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                    beat.done ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-600" : "text-muted-foreground"
                  }`}
                >
                  {beat.done ? <Check className="h-4 w-4" /> : String(index + 1).padStart(2, "0")}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold">{beat.title}</h3>
                        {beat.done && (
                          <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600">
                            Completed
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">Expected: {beat.expect}</p>
                    </div>

                    <button
                      type="button"
                      onClick={() => void runBeat(beat.id)}
                      disabled={isBusy}
                      className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isRunning ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Running...
                        </>
                      ) : beat.done ? (
                        <>
                          <RotateCcw className="h-4 w-4" />
                          Run again
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          Run beat
                        </>
                      )}
                    </button>
                  </div>

                  {beat.labels.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {beat.labels.map((label) => (
                        <span key={label} className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                          {label}
                        </span>
                      ))}
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => setExpandedBeat(isExpanded ? null : beat.id)}
                    className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-muted-foreground transition hover:text-foreground"
                  >
                    <ChevronDown className={`h-4 w-4 transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                    {isExpanded ? "Hide details" : "Show details"}
                  </button>

                  {isExpanded && (
                    <div className="mt-3 rounded-xl border bg-muted/30 p-4">
                      <p className="text-sm leading-6 text-muted-foreground">{beat.narration}</p>
                    </div>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}