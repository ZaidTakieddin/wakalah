"""The demo, as data.

The Resource & Tooling Guide is blunt about this: live API calls fail at the
worst moment. So the demo is a scripted timeline the presenter drives, not an
improvisation — the same beats, in the same order, with the same narration,
every run. What is *not* scripted is the outcome: every verdict below is
produced by the real agent, real CAMARA calls and the real policy engine.

Persona note (honesty ledger, docs/04 section 5): the Nokia simulators have
fixed behaviour per number, so one number cannot flip from clean to compromised
mid-demo. The takeover is therefore staged across two personas and labelled as
such — the signals themselves are real.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

CLEAN_MSISDN = "+99999991001"
COMPROMISED_MSISDN = "+99999991000"
UNAVAILABLE_MSISDN = "+99999990503"

BeatKind = Literal["mandate", "transaction", "operator_event"]


@dataclass(frozen=True)
class Beat:
    """One step of the story."""

    id: str
    title: str
    narration: str
    kind: BeatKind
    expect: str
    """What should happen — shown on screen so the audience knows what to watch
    for, and so a wrong outcome is obvious rather than glossed over."""

    payload: dict[str, Any] = field(default_factory=dict)
    labels: list[str] = field(default_factory=list)
    """Honesty labels rendered with the beat, e.g. 'simulated operator event'."""


SCRIPT: list[Beat] = [
    Beat(
        id="mandate",
        title="Amina authorizes her agent",
        narration=(
            "Amina wants her AI agent to send her mother 2,000 QAR a month. She "
            "authorizes it once. The operator confirms who is registered to this "
            "number, so she never types her identity."
        ),
        kind="mandate",
        expect="A scoped, expiring mandate, with identity autofilled by the operator",
        payload={
            "principalMsisdn": CLEAN_MSISDN,
            "agentId": "agent_rasheed",
            "agentKeyFingerprint": "fp_rasheed_ed25519",
            "amountLimit": 2000,
            "currency": "QAR",
            "beneficiaryIds": ["ben_mother", "ben_landlord"],
        },
        labels=["real CAMARA KYC Fill-in call", "Nokia simulator device"],
    ),
    Beat(
        id="routine",
        title="The monthly remittance",
        narration=(
            "Her agent sends the usual amount to the usual beneficiary. Low risk, "
            "so the agent runs a short verification plan — checking costs money "
            "and latency, and a routine payment does not deserve the full battery."
        ),
        kind="transaction",
        expect="ALLOW, on a small plan",
        payload={
            "transactionId": "demo_tx_routine",
            "amount": {"value": 150, "currency": "QAR"},
            "beneficiaryId": "ben_mother",
            "beneficiaryIsNew": False,
        },
        labels=["real CAMARA calls", "Nokia simulator device"],
    ),
    Beat(
        id="stepup",
        title="A larger transfer, first time to this beneficiary",
        narration=(
            "A bigger amount, and the first payment to her landlord — someone the "
            "mandate permits but she has never paid before. The agent widens the "
            "plan considerably. Nothing is actually wrong, so the answer is not a "
            "refusal, it is a challenge. False declines cost real customers."
        ),
        kind="transaction",
        expect="CHALLENGE (step-up), on a much wider plan than the routine beat",
        payload={
            "transactionId": "demo_tx_stepup",
            "amount": {"value": 1500, "currency": "QAR"},
            "beneficiaryId": "ben_landlord",
            "beneficiaryIsNew": True,
        },
        labels=["real CAMARA calls", "Nokia simulator device"],
    ),
    Beat(
        id="out_of_scope",
        title="The agent tries to pay someone it was never authorized to pay",
        narration=(
            "This is what a scoped mandate buys you. The agent asks to pay an "
            "account outside its authorization. No telecom signal is even needed: "
            "the mandate itself does not permit it. Credentials would have let "
            "this through — a mandate does not."
        ),
        kind="transaction",
        expect="DENY, BENEFICIARY_NOT_PERMITTED",
        payload={
            "transactionId": "demo_tx_out_of_scope",
            "amount": {"value": 400, "currency": "QAR"},
            "beneficiaryId": "ben_unknown_account",
            "beneficiaryIsNew": True,
        },
        labels=["mandate scope check — no network call required to refuse"],
    ),
    Beat(
        id="hijack_event",
        title="The operator reports a SIM swap",
        narration=(
            "A fraudster swaps Amina's SIM. The operator pushes that event to "
            "Wakalah machine-to-machine — the attacker is never asked to approve "
            "anything. Every outstanding mandate is revoked and the principal "
            "drops into challenge-only mode."
        ),
        kind="operator_event",
        expect="Mandate revoked in seconds; principal in challenge-only mode",
        payload={"reason": "sim_swap_detected"},
        labels=[
            "simulated operator event — the sandbox cannot flip a number's state",
            "the revocation itself is real",
        ],
    ),
    Beat(
        id="cloned_agent",
        title="The cloned agent tries to pay itself",
        narration=(
            "The fraudster's copy of the agent presents stolen credentials and "
            "asks for a large transfer. Wakalah checks the hijacked line: SIM "
            "swapped, device swapped, calls being forwarded, the subscriber behind "
            "the number changed. The mandate is already dead."
        ),
        kind="transaction",
        expect="DENY, with hijack and continuity reason codes",
        payload={
            "transactionId": "demo_tx_cloned",
            "amount": {"value": 1800, "currency": "QAR"},
            "beneficiaryId": "ben_attacker",
            "beneficiaryIsNew": True,
            "useCompromisedPersona": True,
        },
        labels=["real CAMARA calls against the compromised persona"],
    ),
    Beat(
        id="degraded",
        title="When the network cannot answer",
        narration=(
            "Finally: an operator outage. Wakalah does not guess and does not wave "
            "the payment through. Missing evidence is absence of evidence, so the "
            "answer is a challenge."
        ),
        kind="transaction",
        expect="CHALLENGE, with INSUFFICIENT_EVIDENCE",
        payload={
            "transactionId": "demo_tx_degraded",
            "amount": {"value": 600, "currency": "QAR"},
            "beneficiaryId": "ben_mother",
            "beneficiaryIsNew": False,
            "useUnavailablePersona": True,
        },
        labels=["Nokia error-simulator device — real 5xx responses"],
    ),
]

BEATS: dict[str, Beat] = {beat.id: beat for beat in SCRIPT}
