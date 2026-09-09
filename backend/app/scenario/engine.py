"""Runs the demo script.

Each beat is announced on the event bus before it executes, so the UI can show
the narration and what to watch for, then show the real result underneath. The
presenter drives it beat by beat; nothing runs on a wall clock, so a run can be
paused, repeated, or resumed mid-story without drifting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.events import beat_scope, bus
from app.scenario.script import BEATS, SCRIPT, Beat


@dataclass
class BeatResult:
    beat_id: str
    title: str
    ok: bool
    summary: str
    detail: dict[str, Any] = field(default_factory=dict)


class ScenarioEngine:
    """Executes beats against the service's own API handlers."""

    def __init__(self) -> None:
        self.mandate_id: str | None = None
        self.compromised_mandate_id: str | None = None
        self.results: list[BeatResult] = []

    # ------------------------------------------------------------------ state
    def reset(self) -> None:
        self.mandate_id = None
        self.compromised_mandate_id = None
        self.results = []
        bus.publish("scenario.reset", {"beats": [b.id for b in SCRIPT]})

    def status(self) -> dict[str, Any]:
        done = {r.beat_id for r in self.results}
        return {
            "beats": [
                {
                    "id": b.id,
                    "title": b.title,
                    "narration": b.narration,
                    "expect": b.expect,
                    "labels": b.labels,
                    "kind": b.kind,
                    "done": b.id in done,
                }
                for b in SCRIPT
            ],
            "mandateId": self.mandate_id,
            "results": [r.__dict__ for r in self.results],
        }

    # -------------------------------------------------------------------- run
    async def run(self, beat_id: str, runner: BeatRunner) -> BeatResult:
        beat = BEATS.get(beat_id)
        if beat is None:
            raise KeyError(beat_id)

        bus.publish(
            "scenario.beat.started",
            {
                "beat_id": beat.id,
                "title": beat.title,
                "narration": beat.narration,
                "expect": beat.expect,
                "labels": beat.labels,
            },
        )
        # Everything the beat triggers — evaluations, network calls, mandate
        # changes — carries this beat's id on the stream from here on.
        with beat_scope(beat.id):
            result = await runner.execute(beat, self)
        self.results = [r for r in self.results if r.beat_id != beat.id] + [result]
        bus.publish("scenario.beat.finished", result.__dict__)
        return result

    async def run_all(self, runner: BeatRunner) -> list[BeatResult]:
        """Run the whole story in order — used for rehearsals and CI-style checks."""
        self.reset()
        return [await self.run(beat.id, runner) for beat in SCRIPT]


class BeatRunner:
    """How a beat actually gets executed.

    Kept separate from the engine so the scenario logic does not import the API
    layer (which imports the scenario engine): the runner is supplied by
    app/main.py at call time.
    """

    async def execute(self, beat: Beat, engine: ScenarioEngine) -> BeatResult:
        raise NotImplementedError


scenario = ScenarioEngine()
