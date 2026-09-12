"""Wire-contract tests for typed events (CLAUDE.md invariant 4, docs/10 §5).

The event schemas in app/models/events.py are the contract between backend and
every UI. These tests pin exactly what lands on the stream: envelope shape,
camelCase wire keys, and loud failure for unregistered event types.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.api.schemas import EvaluateResponse
from app.events import EventBus
from app.models.events import PAYLOAD_MODELS, encode_payload


# ------------------------------------------------------------- wire formats
def test_nac_call_uses_the_documented_camelcase_keys() -> None:
    payload = encode_payload(
        "nac.call",
        {
            "signal": "sim_swap",
            "path": "/passthrough/camara/v1/sim-swap/sim-swap/v0/check",
            "request": {"phoneNumber": "+99999991001"},
            "response": {"swapped": False},
            "status": 200,
            "latency_ms": 42,
            "source": "live",
            "simulated_device": True,
        },
    )

    assert payload["latencyMs"] == 42
    assert payload["simulatedDevice"] is True
    assert "latency_ms" not in payload
    assert "simulated_device" not in payload


def test_agent_trace_carries_transaction_and_latency_in_camel_case() -> None:
    # Producers merge TraceStep.model_dump() under an explicit transactionId:
    payload = encode_payload(
        "agent.trace",
        {
            "transactionId": "tx_1",
            "step": "classify_risk",
            "summary": "Risk classified HIGH",
            "detail": {"agent_tier": "high"},
            "brain": None,
            "degraded": True,
            "latency_ms": 6100,
        },
    )

    assert payload["transactionId"] == "tx_1"
    assert payload["latencyMs"] == 6100
    assert payload["degraded"] is True


def test_transaction_started_names_number_and_beneficiary() -> None:
    """The panel-opening event carries the request's identifying facts, so the
    UI never has to squeeze a principal name into a phone slot."""
    payload = encode_payload(
        "transaction.started",
        {
            "transactionId": "tx_1",
            "amount": 1500,
            "currency": "QAR",
            "beneficiaryId": "ben_landlord",
            "beneficiaryIsNew": True,
            "principal": "",
            "msisdn": "+99999991001",
        },
    )

    assert payload["beneficiaryId"] == "ben_landlord"
    assert payload["msisdn"] == "+99999991001"


def test_scenario_beat_finished_reports_beat_id_camel_case() -> None:
    payload = encode_payload(
        "scenario.beat.finished",
        {"beat_id": "routine", "title": "t", "ok": True, "summary": "s", "detail": {}},
    )
    assert payload["beatId"] == "routine"


def test_decision_final_reuses_the_partner_response_schema() -> None:
    """'One schema feeding both the WebSocket stream and the audit trail':
    decision.final on the stream IS the partner-facing EvaluateResponse."""
    response = EvaluateResponse(
        transaction_id="tx_1",
        decision="challenge",
        risk_tier="high",
        reason_codes=["AGENT_REQUESTED_STEP_UP"],
        rationale="r",
        agent_proposal="challenge",
        decided_at="2026-08-06T12:50:24+00:00",
        latency_ms=20936,
    )
    payload = encode_payload("decision.final", response.model_dump(mode="json", by_alias=True))

    assert payload["policyVersion"] == "v1"
    assert payload["policyOverrodeAgent"] is False
    assert payload["reasonCodes"] == ["AGENT_REQUESTED_STEP_UP"]


# ------------------------------------------------------------ bus behaviour
def test_bus_wraps_every_event_in_the_documented_envelope() -> None:
    bus = EventBus()

    bus.publish(
        "mandate.revoked",
        {"mandateId": "man_1", "reason": "sim_swap_detected", "status": "revoked"},
    )

    (event,) = bus.recent()
    assert set(event) == {"type", "ts", "payload"}
    assert event["type"] == "mandate.revoked"
    datetime.fromisoformat(event["ts"])  # ISO timestamp, parseable
    assert event["payload"]["mandateId"] == "man_1"


def test_untyped_event_types_fail_loudly_at_publish() -> None:
    bus = EventBus()

    with pytest.raises(ValueError, match="untyped event"):
        bus.publish("mystery.event", {"anything": True})
    assert bus.recent() == []


def test_every_registered_event_type_is_importable_and_named_by_string() -> None:
    expected = {
        "nac.call",
        "agent.trace",
        "transaction.started",
        "decision.final",
        "mandate.updated",
        "mandate.revoked",
        "mandate.changed_mid_flight",
        "scenario.beat.started",
        "scenario.beat.finished",
        "scenario.reset",
    }
    assert set(PAYLOAD_MODELS) == expected


# ------------------------------------------------------- ambient correlation
def test_scopes_attach_ids_to_schemas_that_declare_them() -> None:
    from app.events import EventBus, beat_scope, transaction_scope

    bus = EventBus()
    with beat_scope("stepup"), transaction_scope("tx_9"):
        bus.publish(
            "nac.call",
            {
                "signal": "sim_swap",
                "path": "/check",
                "request": {},
                "response": {"swapped": False},
                "status": 200,
            },
        )

    payload = bus.recent()[-1]["payload"]
    assert payload["beatId"] == "stepup"
    assert payload["transactionId"] == "tx_9"


def test_absent_scope_means_absent_keys_never_nulls() -> None:
    from app.events import EventBus

    bus = EventBus()
    bus.publish(
        "nac.call",
        {
            "signal": "sim_swap",
            "path": "/check",
            "request": {},
            "response": {"swapped": False},
            "status": 200,
        },
    )

    payload = bus.recent()[-1]["payload"]
    assert "beatId" not in payload
    assert "transactionId" not in payload


def test_explicit_ids_win_over_ambient_scopes() -> None:
    from app.events import EventBus, beat_scope, transaction_scope

    bus = EventBus()
    with beat_scope("stepup"), transaction_scope("tx_9"):
        bus.publish(
            "agent.trace",
            {
                "transactionId": "tx_explicit",
                "step": "decide",
                "summary": "done",
            },
        )

    payload = bus.recent()[-1]["payload"]
    assert payload["transactionId"] == "tx_explicit"
    assert payload["beatId"] == "stepup"


def test_scopes_reset_after_the_block() -> None:
    from app.events import EventBus, beat_scope, current_beat_id

    bus = EventBus()
    with beat_scope("routine"):
        assert current_beat_id() == "routine"
    assert current_beat_id() is None

    bus.publish(
        "mandate.revoked",
        {"mandateId": "man_1", "reason": "x", "status": "revoked"},
    )
    assert "beatId" not in bus.recent()[-1]["payload"]
