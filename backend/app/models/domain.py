"""The vocabulary of Wakalah.

Every other module speaks these types. They encode the design decisions from
docs/04 (concept spec) so the code cannot drift from the documented design:

    * a signal always belongs to one of five trust dimensions
    * evidence is always normalized — never raw provider JSON
    * a verdict is always one of three values, never free prose
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Timezone-aware current time. Never use naive datetimes in evidence."""
    return datetime.now(UTC)


# ---------------------------------------------------------------- dimensions
class TrustDimension(StrEnum):
    """The five questions any honest trust system must answer (docs/04 section 3)."""

    BINDING = "binding"  # is this number's SIM actually here?
    IDENTITY = "identity"  # who is the registered owner?
    HIJACK = "hijack"  # has the account been taken over recently?
    CONTINUITY = "continuity"  # is this still the same human over time?
    CONTEXT = "context"  # is the situation consistent right now?


class Signal(StrEnum):
    """The CAMARA signals Wakalah consumes, by internal name."""

    NUMBER_VERIFICATION = "number_verification"
    KYC_MATCH = "kyc_match"
    SIM_SWAP = "sim_swap"
    DEVICE_SWAP = "device_swap"
    CALL_FORWARDING = "call_forwarding"
    NUMBER_RECYCLING = "number_recycling"
    TENURE = "tenure"
    REACHABILITY = "reachability"
    ROAMING = "roaming"
    LOCATION_VERIFICATION = "location_verification"


SIGNAL_DIMENSION: dict[Signal, TrustDimension] = {
    Signal.NUMBER_VERIFICATION: TrustDimension.BINDING,
    Signal.KYC_MATCH: TrustDimension.IDENTITY,
    Signal.SIM_SWAP: TrustDimension.HIJACK,
    Signal.DEVICE_SWAP: TrustDimension.HIJACK,
    Signal.CALL_FORWARDING: TrustDimension.HIJACK,
    Signal.NUMBER_RECYCLING: TrustDimension.CONTINUITY,
    Signal.TENURE: TrustDimension.CONTINUITY,
    Signal.REACHABILITY: TrustDimension.CONTEXT,
    Signal.ROAMING: TrustDimension.CONTEXT,
    Signal.LOCATION_VERIFICATION: TrustDimension.CONTEXT,
}

CORE_SPINE: frozenset[Signal] = frozenset(
    {
        Signal.NUMBER_VERIFICATION,
        Signal.KYC_MATCH,
        Signal.SIM_SWAP,
        Signal.DEVICE_SWAP,
    }
)
"""Run on essentially every mandate/verification (docs/04 section 3)."""

ESCALATION_TOOLKIT: frozenset[Signal] = frozenset(Signal) - CORE_SPINE
"""Pulled by the agent's verification plan only when risk warrants it."""


# ---------------------------------------------------------------- decisions
class RiskTier(StrEnum):
    """The agent's classification of a requested action."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verdict(StrEnum):
    """The final outcome. `REVIEW` is documented as a production extension
    (a human queue for very large amounts); the demo uses three."""

    ALLOW = "allow"
    STEP_UP = "step_up"
    DENY = "deny"


class EvidenceSource(StrEnum):
    """Where a piece of evidence actually came from.

    This drives the demo's honesty labelling: the UI renders the label from the
    data itself, so it can never drift from what really happened.
    """

    LIVE = "live"  # a real call to the network, right now
    CACHED = "cached"  # a real response, reused within its TTL
    REPLAY = "replay"  # a real response recorded in an earlier run
    SIMULATED = "simulated"  # fabricated by us; always labelled as such
    UNAVAILABLE = "unavailable"  # the signal could not be obtained


class ConsentStatus(StrEnum):
    """Consent state for this use of subscriber data. Markets differ: some
    permit fraud checks under legitimate interest, others require explicit
    runtime consent."""

    GRANTED = "granted"
    NOT_REQUIRED_AT_RUNTIME = "not_required_at_runtime"
    MISSING = "missing"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------- evidence
class EvidenceRecord(BaseModel):
    """One normalized network signal.

    `app/nac/` emits only this shape — never raw provider JSON. That is what
    keeps operator and provider differences out of the policy engine, and what
    lets every decision be reconstructed later (docs/07 section 3.5).
    """

    model_config = ConfigDict(frozen=True)

    signal: Signal
    dimension: TrustDimension
    provider: str = "nokia_nac"
    network: str | None = None

    subject: dict[str, str] = Field(default_factory=dict)
    """Device identifier used, e.g. {"phoneNumber": "+99999991001"}."""

    result: dict[str, Any] = Field(default_factory=dict)
    """The normalized answer, e.g. {"swapped": true, "latestChange": "..."}."""

    purpose: str = "FraudPreventionAndDetection"
    legal_basis: str = "legitimate_interest"
    consent_status: ConsentStatus = ConsentStatus.NOT_REQUIRED_AT_RUNTIME

    evidence_time: datetime = Field(default_factory=utc_now)
    source: EvidenceSource = EvidenceSource.LIVE
    latency_ms: int | None = None

    ok: bool = True
    error_code: str | None = None
    error_message: str | None = None

    @property
    def is_usable(self) -> bool:
        """False when the signal failed — the policy engine must treat a missing
        signal as absence of evidence, never as a pass."""
        return self.ok and self.source is not EvidenceSource.UNAVAILABLE


class EvidenceBundle(BaseModel):
    """Everything gathered for one decision, keyed by signal."""

    records: dict[Signal, EvidenceRecord] = Field(default_factory=dict)

    def add(self, record: EvidenceRecord) -> None:
        self.records[record.signal] = record

    def get(self, signal: Signal) -> EvidenceRecord | None:
        return self.records.get(signal)

    def usable_signals(self) -> set[Signal]:
        return {s for s, r in self.records.items() if r.is_usable}

    def covered_dimensions(self) -> set[TrustDimension]:
        return {SIGNAL_DIMENSION[s] for s in self.usable_signals()}


# ---------------------------------------------------------------- mandates
class MandateStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    CHALLENGE_ONLY = "challenge_only"
    """After a detected hijack: everything requires step-up until secure
    re-verification clears it (docs/04 section 4)."""


class MandateScope(BaseModel):
    """What the agent is allowed to do — the limits of the wakalah contract."""

    action: str = "money_transfer"
    amount_limit: float
    currency: str = "QAR"
    period: str = "month"
    beneficiary_ids: list[str] = Field(default_factory=list)
    """Empty means unrestricted; the demo always restricts."""


class Mandate(BaseModel):
    """A principal's authorization of one agent, with limits and an expiry."""

    mandate_id: str
    principal_id: str  # hashed MSISDN — raw numbers are not stored
    principal_msisdn: str  # sandbox only; production stores the hash alone
    agent_id: str
    agent_key_fingerprint: str
    """The token is bound to this keypair: a stolen token is useless without
    the matching private key (sender-constrained / DPoP-style)."""

    scope: MandateScope
    status: MandateStatus = MandateStatus.ACTIVE
    risk_score: float = 0.0
    evidence_refs: list[str] = Field(default_factory=list)
    policy_version: str = "v1"
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    revoked_reason: str | None = None


class TransactionRequest(BaseModel):
    """What a partner (bank/PSP/merchant) submits for evaluation."""

    transaction_id: str
    mandate_id: str
    partner_id: str = "demo_psp"
    action: str = "money_transfer"
    amount: float
    currency: str = "QAR"
    beneficiary_id: str
    beneficiary_is_new: bool = False
    channel: dict[str, str] = Field(default_factory=dict)
    requested_at: datetime = Field(default_factory=utc_now)


# ---------------------------------------------------------------- outcomes
class VerificationPlan(BaseModel):
    """The checks the agent chose to run for this transaction.

    The agent proposes; the policy engine enforces a per-tier minimum floor and
    may add signals back. It can never plan below the floor (docs/04 section 4).
    """

    risk_tier: RiskTier
    signals: list[Signal]
    rationale: str = ""
    proposed_by: str = "risk_analyst"


class Decision(BaseModel):
    """The final answer returned to the partner."""

    transaction_id: str
    verdict: Verdict
    risk_tier: RiskTier
    reason_codes: list[str] = Field(default_factory=list)
    """Stable machine-readable strings (e.g. SIM_SWAP_RECENT) so partners can
    build rules on them; they also render as the human 'why' in the UI."""

    rationale: str = ""
    agent_proposal: Verdict | None = None
    """What the AI proposed, before policy. Kept so the demo can show the two
    side by side — 'AI proposes, policy disposes' made visible."""

    policy_version: str = "v1"
    evidence: EvidenceBundle = Field(default_factory=EvidenceBundle)
    decided_at: datetime = Field(default_factory=utc_now)
    latency_ms: int | None = None
