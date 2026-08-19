"""What each specialist agent must return.

These are the typed contracts that stop an agent answering a payments question
with a paragraph of prose. If a model returns anything that does not fit, the
validation fails and the brain router falls through to the next brain — the
system never acts on a malformed decision.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.domain import RiskTier, Signal, Verdict


class RiskAssessment(BaseModel):
    """Output of the Risk Analyst."""

    risk_tier: RiskTier
    rationale: str = Field(description="One or two sentences, plain language.")
    factors: list[str] = Field(
        default_factory=list,
        description="The specific facts that drove the classification.",
    )


class PlanProposal(BaseModel):
    """Output of the Plan Builder."""

    signals: list[Signal] = Field(description="Which checks to run for this request.")
    rationale: str = Field(description="Why these checks, and why not others.")


class EvidenceInterpretation(BaseModel):
    """Output of the Evidence Interpreter."""

    proposed_verdict: Verdict
    rationale: str = Field(description="What the combination of signals means.")
    concerns: list[str] = Field(
        default_factory=list, description="Specific findings that worried the agent."
    )


class TraceStep(BaseModel):
    """One visible step of the agent's reasoning.

    The Tooling Guide's own advice is to show the agent's reasoning trace on
    screen, so this is a product feature, not a debug log.
    """

    step: str
    summary: str
    detail: dict = Field(default_factory=dict)
    brain: str | None = None
    degraded: bool = False
    latency_ms: int | None = None
