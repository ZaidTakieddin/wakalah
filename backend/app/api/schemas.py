"""The partner-facing API contract (docs/07 section 3.5).

Deliberately separate types from `app/models/domain.py`. Partners integrate
against these shapes, so they must stay stable even when internals are
refactored — and they are camelCase because that is what the rest of the
payments world speaks.

One vocabulary mapping worth knowing: internally the middle verdict is
`step_up`; externally it is `challenge`, which is the industry term and the
value documented in the contract. The translation happens here, at the boundary,
and nowhere else.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import Decision, EvidenceBundle, Verdict

PartnerDecision = Literal["allow", "challenge", "deny"]

VERDICT_TO_PARTNER: dict[Verdict, PartnerDecision] = {
    Verdict.ALLOW: "allow",
    Verdict.STEP_UP: "challenge",
    Verdict.DENY: "deny",
}


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


class ApiModel(BaseModel):
    """camelCase on the wire, snake_case in Python."""

    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)


# ------------------------------------------------------------------ requests
class Amount(ApiModel):
    value: float
    currency: str = "QAR"


class EvaluateRequest(ApiModel):
    """What a bank, PSP or merchant submits before honouring an agent action."""

    transaction_id: str
    mandate_id: str
    partner_id: str = "demo_psp"
    action: str = "money_transfer"
    amount: Amount
    beneficiary_id: str
    beneficiary_is_new: bool = False
    channel: dict[str, str] = Field(default_factory=dict)
    agent_signature: str | None = Field(
        default=None,
        description=(
            "Proof of possession: the agent signs the request with the private "
            "key its mandate is bound to. Design-complete; verification lands "
            "with the sender-constrained token work."
        ),
    )


class CreateMandateRequest(ApiModel):
    """Mandate creation. In production the principal completes the operator
    consent flow (Number Verification) first; the sandbox auto-approves it."""

    principal_name: str = Field(
        default="",
        description=(
            "Optional. Left empty, the operator's registered identity is used "
            "(CAMARA KYC Fill-in) so the principal need not type it."
        ),
    )
    principal_msisdn: str
    agent_id: str
    agent_key_fingerprint: str
    amount_limit: float
    currency: str = "QAR"
    beneficiary_ids: list[str] = Field(default_factory=list)


# ----------------------------------------------------------------- responses
class SignalEvidence(ApiModel):
    """One signal as a partner sees it: the answer plus its provenance."""

    dimension: str
    result: dict[str, Any] = Field(default_factory=dict)
    source: str
    """live | cached | replay | simulated | unavailable — the honesty label."""
    available: bool = True
    error_code: str | None = None


class Challenge(ApiModel):
    challenge_id: str
    method: str = "step_up_number_verification"


class EvaluateResponse(ApiModel):
    transaction_id: str
    decision: PartnerDecision
    risk_tier: str
    reason_codes: list[str] = Field(default_factory=list)
    rationale: str = ""
    evidence_summary: dict[str, SignalEvidence] = Field(default_factory=dict)
    challenge: Challenge | None = None
    policy_version: str = "v1"
    agent_proposal: PartnerDecision | None = Field(
        default=None,
        description=(
            "What the AI proposed before the deterministic policy engine ruled. "
            "Exposed so the split is auditable, not just claimed."
        ),
    )
    policy_overrode_agent: bool = False
    decided_at: str
    latency_ms: int | None = None
    beat_id: str | None = Field(
        default=None,
        description=(
            "Which scenario beat produced this decision, when decided inside "
            "one. Attached by the event bus on decision.final only — the REST "
            "response carries null outside beats, keeping the stored audit "
            "record free of demo scaffolding."
        ),
    )

    @classmethod
    def from_decision(
        cls, decision: Decision, *, latency_ms: int | None = None
    ) -> EvaluateResponse:
        partner_verdict = VERDICT_TO_PARTNER[decision.verdict]
        agent_proposal = (
            VERDICT_TO_PARTNER[decision.agent_proposal]
            if decision.agent_proposal is not None
            else None
        )
        return cls(
            transaction_id=decision.transaction_id,
            decision=partner_verdict,
            risk_tier=decision.risk_tier.value,
            reason_codes=decision.reason_codes,
            rationale=decision.rationale,
            evidence_summary=_summarise(decision.evidence),
            challenge=(
                Challenge(challenge_id=f"chl_{decision.transaction_id}")
                if decision.verdict is Verdict.STEP_UP
                else None
            ),
            policy_version=decision.policy_version,
            agent_proposal=agent_proposal,
            policy_overrode_agent=(
                agent_proposal is not None and agent_proposal != partner_verdict
            ),
            decided_at=decision.decided_at.isoformat(),
            latency_ms=latency_ms,
        )


class MandateResponse(ApiModel):
    mandate_id: str
    principal_id: str
    agent_id: str
    status: str
    amount_limit: float
    currency: str
    beneficiary_ids: list[str] = Field(default_factory=list)
    created_at: str


def _summarise(evidence: EvidenceBundle) -> dict[str, SignalEvidence]:
    return {
        signal.value: SignalEvidence(
            dimension=record.dimension.value,
            result=record.result,
            source=record.source.value,
            available=record.is_usable,
            error_code=record.error_code,
        )
        for signal, record in evidence.records.items()
    }
