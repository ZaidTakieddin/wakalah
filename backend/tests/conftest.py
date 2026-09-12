"""Shared fixtures for the offline test suites.

Every suite mandated by backend/CLAUDE.md §Tests must run with no network, no
LLM keys and no database — the same way the demo survives a dead venue:

    * NacClient runs in `replay` mode against backend/replay_cache/
    * BrainRouter is replaced by a deterministic stub (no model is contacted)
    * AuditTrail is pinned to its in-memory backend

The stubs keep the *shape* of the real agents: classification and planning use
the supervisor's own policy-shaped heuristics, so what gets tested is the wiring
(graph order, event stream, contracts), not anyone's prose.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from typing import Any

import pytest

import app.store.memory as memory
from app.agents import supervisor as supervisor_module
from app.agents.brains import BrainResult, BrainRouter
from app.agents.schemas import EvidenceInterpretation
from app.config import settings
from app.events import bus
from app.models.domain import RiskTier, Verdict
from app.scenario.engine import scenario as engine
from app.store.audit import audit
from app.store.memory import DecisionStore, MandateStore


# ------------------------------------------------------------------ brain stubs
class HeuristicOnlyBrains(BrainRouter):
    """Answers every agent node with its own deterministic heuristic.

    `degraded=True` on every step — which is exactly the honest labelling the
    production system shows when no LLM answers.
    """

    async def think(
        self,
        *,
        instructions: str,
        prompt: str,
        output_type: Any,
        heuristic: Any,
    ) -> BrainResult:
        return BrainResult(output=heuristic, brain="heuristic", degraded=True)


class TierAwareBrains(HeuristicOnlyBrains):
    """Heuristic-only, plus one live-agent behaviour: proposing caution.

    In the demo the Gemini interpreter proposes STEP_UP on medium/high-risk
    transactions even when every signal comes back clean, which exercises the
    AGENT_REQUESTED_STEP_UP escalation path (docs/10 §8 'stepup' beat). This
    stub reproduces that single behaviour deterministically by reading the risk
    tier line from the supervisor's own prompt format.
    """

    async def think(
        self,
        *,
        instructions: str,
        prompt: str,
        output_type: Any,
        heuristic: Any,
    ) -> BrainResult:
        if (
            output_type is EvidenceInterpretation
            and isinstance(heuristic, EvidenceInterpretation)
            and heuristic.proposed_verdict is Verdict.ALLOW
        ):
            match = re.search(r"Risk tier:\s*(\w+)", prompt)
            if match and match.group(1) != RiskTier.LOW.value:
                return BrainResult(
                    output=EvidenceInterpretation(
                        proposed_verdict=Verdict.STEP_UP,
                        rationale=(
                            "Stub interpreter: a medium/high-tier transfer "
                            "deserves verification even when signals are clean."
                        ),
                        concerns=["tier_escalation"],
                    ),
                    brain="heuristic",
                    degraded=True,
                )
        return await super().think(
            instructions=instructions, prompt=prompt, output_type=output_type, heuristic=heuristic
        )


# --------------------------------------------------------------------- helpers
def fresh_state() -> None:
    """Reset every process-wide singleton a run touches."""
    memory.mandates = MandateStore()
    memory.decisions = DecisionStore()
    engine.reset()


VOLATILE_EVENT_KEYS = frozenset(
    {"ts", "latency_ms", "latencyMs", "decidedAt", "createdAt", "evidence_time"}
)
"""Fields that legitimately differ between two identical runs (timings) plus
auto-incremented identifiers, normalized away before comparing sequences."""

MANDATE_ID_RE = re.compile(r"man_\d+_[0-9a-f]+")


def scrub_volatile(node: Any) -> Any:
    """Return a copy of `node` with timing fields blanked and mandate ids
    canonicalized, so two deterministic runs compare equal."""
    if isinstance(node, dict):
        return {
            key: scrub_volatile(value)
            for key, value in node.items()
            if key not in VOLATILE_EVENT_KEYS
        }
    if isinstance(node, list):
        return [scrub_volatile(item) for item in node]
    if isinstance(node, str):
        return MANDATE_ID_RE.sub("man_X", node)
    return node


def normalize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [scrub_volatile(deepcopy(event)) for event in events]


@contextmanager
def capture_events() -> Iterator[list[dict[str, Any]]]:
    """Collect everything published to the bus while the block runs."""
    queue = bus.subscribe()
    captured: list[dict[str, Any]] = []
    try:
        yield captured
        while True:
            try:
                captured.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                break
    finally:
        bus.unsubscribe(queue)


# -------------------------------------------------------------------- fixtures
@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch the environment to fully-offline and reset shared state."""
    monkeypatch.setattr(settings, "nac_mode", "replay")
    monkeypatch.setattr(settings, "nac_record", False)
    monkeypatch.setattr(audit, "_enabled", False)
    monkeypatch.setattr(audit, "_failed", False)
    fresh_state()


@pytest.fixture
def offline_app(offline: None, monkeypatch: pytest.MonkeyPatch) -> Any:
    """The real FastAPI app: replay evidence, no LLMs, no Supabase."""
    monkeypatch.setattr(supervisor_module, "BrainRouter", HeuristicOnlyBrains)
    from app.main import app

    return app


@pytest.fixture
def tier_aware_app(offline: None, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Like offline_app, but the stub interpreter escalates medium/high tiers."""
    monkeypatch.setattr(supervisor_module, "BrainRouter", TierAwareBrains)
    from app.main import app

    return app
