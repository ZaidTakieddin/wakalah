"""Scenario determinism tests (backend/CLAUDE.md §Tests).

Two properties are enforced here:

    1. Determinism — the same scripted input produces the identical event
       sequence, twice. Timing and auto-incremented ids are normalized away;
       everything else must match byte for byte.
    2. The story lands where docs/10 §8 says it does — the beats a presenter
       relies on in front of judges cannot silently drift.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.scenario.script import SCRIPT
from tests.conftest import capture_events, fresh_state, normalize_events


def _run_all(app: Any) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Run the full script against the real endpoints; return (events, by-id)."""
    fresh_state()
    with TestClient(app) as client:
        client.post("/v1/scenario/reset")
        with capture_events() as events:
            response = client.post("/v1/scenario/run-all")
    assert response.status_code == 200
    results = response.json()["results"]
    assert [r["beat_id"] for r in results] == [b.id for b in SCRIPT]
    failed = [r for r in results if not r["ok"]]
    assert not failed, f"beats failed: {failed}"
    return events, {r["beat_id"]: r for r in results}


# ---------------------------------------------------------------- determinism
def test_same_scripted_input_produces_identical_event_sequence(offline_app: Any) -> None:
    """The rule as written: same input twice -> identical sequence."""
    first = normalize_events(_run_all(offline_app)[0])
    second = normalize_events(_run_all(offline_app)[0])

    assert first, "no events were captured"
    assert len(first) == len(second)
    assert first == second


def test_every_beat_announces_itself_on_the_stream(offline_app: Any) -> None:
    """Each beat is bracketed by started/finished events, in script order."""
    events, _ = _run_all(offline_app)

    started = [e["payload"]["id"] for e in events if e["type"] == "scenario.beat.started"]
    finished = [e["payload"]["beat_id"] for e in events if e["type"] == "scenario.beat.finished"]
    assert started == [b.id for b in SCRIPT]
    assert finished == [b.id for b in SCRIPT]


def test_reset_clears_the_stage(offline_app: Any) -> None:
    with TestClient(offline_app) as client:
        client.post("/v1/scenario/run-all")
        status = client.post("/v1/scenario/reset").json()
        assert status["results"] == []
        assert all(not b["done"] for b in status["beats"])
        assert status["mandateId"] is None


# ------------------------------------------------------------ documented story
def test_offline_story_outcomes_match_the_demo_contract(offline_app: Any) -> None:
    """The verdict table every presenter memorizes (docs/10 §8).

    Under deterministic fallback brains the numbers come from policy floors,
    not from an LLM's wider plan — so signal counts here are lower bounds that
    must hold no matter how smart or dumb the agent tier is.
    """
    _, by_id = _run_all(offline_app)

    routine = by_id["routine"]["detail"]
    stepup = by_id["stepup"]["detail"]
    out_of_scope = by_id["out_of_scope"]["detail"]
    cloned = by_id["cloned_agent"]["detail"]
    degraded = by_id["degraded"]["detail"]

    # Routine payment: ALLOW on the smallest plan.
    assert routine["decision"] == "allow"
    assert routine["signals"] == ["sim_swap"]

    # Riskier transfer: the plan grows with the tier.
    assert set(routine["signals"]) < set(stepup["signals"])

    # Scope refusal needs no network evidence at all.
    assert out_of_scope["decision"] == "deny"
    assert "BENEFICIARY_NOT_PERMITTED" in out_of_scope["reasonCodes"]

    # Cloned agent against the compromised persona: the takeover pattern denies.
    assert cloned["decision"] == "deny"
    assert "SIM_SWAP_RECENT_HIGH_VALUE" in cloned["reasonCodes"]

    # Degraded network: missing evidence never means approved.
    assert degraded["decision"] == "challenge"
    assert any("INSUFFICIENT_EVIDENCE" in c for c in degraded["reasonCodes"])


def test_agent_caution_escalates_a_clean_medium_risk_transfer(tier_aware_app: Any) -> None:
    """'AI proposes, policy disposes': STEP_UP proposed on clean evidence is
    honoured as AGENT_REQUESTED_STEP_UP — friction up, refusal never."""
    _, by_id = _run_all(tier_aware_app)

    stepup = by_id["stepup"]["detail"]
    assert stepup["decision"] == "challenge"
    assert "AGENT_REQUESTED_STEP_UP" in stepup["reasonCodes"]
    assert stepup["policyOverrodeAgent"] is False
