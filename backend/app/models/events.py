"""Typed events — one schema for every cross-layer message (CLAUDE.md invariant 4).

Every event on the bus feeds two consumers: the WebSocket stream the demo UI
renders, and the audit trail. Ad-hoc dicts let those drift apart silently; a
schema cannot. Each event type below declares its payload once:

    * producers may build payloads in snake_case or camelCase
      (`populate_by_name`), so call sites stay readable Python;
    * the wire format is always camelCase (`by_alias`), matching docs/10 §5 —
      the contract partners and the frontend integrate against;
    * an unregistered event type raises at publish time instead of leaking an
      undocumented shape onto the stream.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas import EvaluateResponse


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


class EventPayload(BaseModel):
    """Base for wire payloads: snake_case inside, camelCase on the stream."""

    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)


# ------------------------------------------------------------------ payloads
class NacCall(EventPayload):
    """One network call as it happened — the live API panel."""

    signal: str
    path: str
    request: dict[str, Any]
    response: Any = None
    status: int | None = None
    latency_ms: int = 0
    source: str = "live"
    simulated_device: bool = False


class AgentTrace(EventPayload):
    """One step of the agent's reasoning — the reasoning trace."""

    transaction_id: str
    step: str
    summary: str
    detail: dict[str, Any] = Field(default_factory=dict)
    brain: str | None = None
    degraded: bool = False
    latency_ms: int | None = None


class TransactionStarted(EventPayload):
    """An evaluation has begun — open the decision panel."""

    transaction_id: str
    amount: float
    currency: str
    beneficiary_is_new: bool = False
    principal: str = ""


class MandateUpdated(EventPayload):
    """A mandate exists (created) — the mandate card."""

    mandate_id: str
    status: str
    identity_autofilled_by_operator: bool = False


class MandateRevoked(EventPayload):
    """The Sentinel fired — the revocation moment."""

    mandate_id: str
    reason: str
    status: str


class MandateChangedMidFlight(EventPayload):
    """Revocation landed while a decision was still being made."""

    transaction_id: str
    status_at_start: str
    status_now: str
    verdict_before: str
    verdict_now: str


class ScenarioBeatStarted(EventPayload):
    """A demo beat begins — the narration card."""

    id: str
    title: str
    narration: str
    expect: str = ""
    labels: list[str] = Field(default_factory=list)


class ScenarioBeatFinished(EventPayload):
    """A demo beat completed — tick it in the timeline."""

    beat_id: str
    title: str
    ok: bool
    summary: str = ""
    detail: dict[str, Any] = Field(default_factory=dict)


class ScenarioReset(EventPayload):
    """The story starts over — clear the stage."""

    beats: list[str] = Field(default_factory=list)


PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    "nac.call": NacCall,
    "agent.trace": AgentTrace,
    "transaction.started": TransactionStarted,
    "decision.final": EvaluateResponse,
    "mandate.updated": MandateUpdated,
    "mandate.revoked": MandateRevoked,
    "mandate.changed_mid_flight": MandateChangedMidFlight,
    "scenario.beat.started": ScenarioBeatStarted,
    "scenario.beat.finished": ScenarioBeatFinished,
    "scenario.reset": ScenarioReset,
}
"""Every event type that may appear on the bus. Adding an event without a
schema here fails loudly at publish time — that is the point."""


def encode_payload(event_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a payload against its schema and render the wire format."""
    model = PAYLOAD_MODELS.get(event_type)
    if model is None:
        raise ValueError(f"untyped event '{event_type}': add a schema to app/models/events.py")
    validated = model.model_validate(payload)
    dumped = validated.model_dump(mode="json", by_alias=True)
    return dumped


__all__ = [
    "PAYLOAD_MODELS",
    "AgentTrace",
    "MandateChangedMidFlight",
    "MandateRevoked",
    "MandateUpdated",
    "NacCall",
    "ScenarioBeatFinished",
    "ScenarioBeatStarted",
    "ScenarioReset",
    "TransactionStarted",
    "encode_payload",
]
