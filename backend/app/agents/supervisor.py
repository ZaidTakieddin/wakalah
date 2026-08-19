"""The Wakalah Supervisor Agent — LangGraph orchestration of four specialists.

    classify_risk    (AI)      what kind of request is this?
    build_plan       (AI)      which checks does it deserve?
    enforce_floor    (POLICY)  ...and which checks does it get regardless?
    gather_evidence  (TOOLS)   call the chosen CAMARA signals
    interpret        (AI)      what does this combination mean?
    decide           (POLICY)  the final, deterministic verdict

The interleaving is the architecture: AI nodes reason, policy nodes bind. An
agent can escalate a request but can never talk the system into checking less
(app/policy/engine.py::baseline_tier).

Every node appends a TraceStep, so the demo can show the reasoning on screen —
which the Resource & Tooling Guide explicitly recommends.
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.agents.brains import BrainRouter
from app.agents.schemas import (
    EvidenceInterpretation,
    PlanProposal,
    RiskAssessment,
    TraceStep,
)
from app.models.domain import (
    CORE_SPINE,
    Decision,
    EvidenceBundle,
    Mandate,
    RiskTier,
    Signal,
    TransactionRequest,
    Verdict,
    VerificationPlan,
)
from app.nac.client import NacClient
from app.policy.engine import PolicyEngine

TraceHook = Callable[[TraceStep], None]

ISSUANCE_ONLY_SIGNALS = frozenset({Signal.NUMBER_VERIFICATION, Signal.KYC_MATCH})
"""Proved once when the mandate is created, never re-run per transaction.

Number Verification needs the operator's 3-legged consent flow, and KYC Match
compares a claimed identity that does not change between transactions. Keeping
them out of the hot path is both correct and cheaper.
"""

RISK_INSTRUCTIONS = """You are the Risk Analyst of Wakalah, a trust layer that
decides whether an AI agent may act on a human principal's behalf.

Classify the requested transaction as low, medium or high risk. Weigh: the
amount against the mandate's limit, whether the beneficiary is new, how the
request arrived, and the principal's mandate status.

Be proportionate. A small routine payment to a known beneficiary is low risk; a
large transfer to a new beneficiary is high risk. Do not inflate every request
to high — over-checking costs real customers real money in false declines."""

PLAN_INSTRUCTIONS = """You are the Plan Builder of Wakalah. Given a risk tier,
choose which telecom signals to verify. Available signals and what they answer:

  HIJACK      sim_swap             - was the number moved to a new SIM recently
              device_swap          - same SIM, new handset
              call_forwarding      - calls being silently intercepted (vishing)
  CONTINUITY  number_recycling     - did the subscriber behind the number change
              tenure               - how long this subscriber has held the number
  CONTEXT     reachability         - is the device alive right now
              roaming              - is the principal genuinely abroad
              location_verification- is the device where it should be

(Binding and identity - number_verification and kyc_match - are proved once when
the mandate is created, not re-run per transaction, so they are not yours to
choose here.)

Low risk: the cheap hijack checks only. Medium: add continuity or context where
it is informative. High: add the signals that expose interception and identity
discontinuity. Choose deliberately and justify the selection - unnecessary calls
cost money and latency."""

INTERPRET_INSTRUCTIONS = """You are the Evidence Interpreter of Wakalah. Read the
gathered signals together, not individually, and propose allow, step_up or deny.

Judgement matters: a device swap alone is weak - people buy phones - but a device
swap plus a recent SIM swap before a large transfer to a new beneficiary is an
account takeover pattern. An out-of-area device while roaming is a traveller, not
a fraudster. A signal that could not be fetched is absence of evidence, never a
pass.

Prefer step_up over deny when signals are mixed: a false decline is a real cost
to a real customer."""


class SupervisorState(BaseModel):
    """State carried through the graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    tx: TransactionRequest
    mandate: Mandate

    risk_tier: RiskTier = RiskTier.LOW
    agent_tier: RiskTier = RiskTier.LOW
    plan: VerificationPlan | None = None
    evidence: EvidenceBundle = Field(default_factory=EvidenceBundle)
    agent_proposal: Verdict | None = None
    agent_rationale: str = ""
    decision: Decision | None = None
    trace: list[TraceStep] = Field(default_factory=list)


class WakalahSupervisor:
    """Builds and runs the decision graph."""

    def __init__(
        self,
        *,
        nac: NacClient,
        policy: PolicyEngine | None = None,
        brains: BrainRouter | None = None,
        on_trace: TraceHook | None = None,
    ) -> None:
        self.nac = nac
        self.policy = policy or PolicyEngine()
        self.brains = brains or BrainRouter()
        self.on_trace = on_trace
        self._graph = self._build_graph()

    # ------------------------------------------------------------------ graph
    def _build_graph(self) -> Any:
        graph = StateGraph(SupervisorState)
        graph.add_node("classify_risk", self._classify_risk)
        graph.add_node("build_plan", self._build_plan)
        graph.add_node("enforce_floor", self._enforce_floor)
        graph.add_node("gather_evidence", self._gather_evidence)
        graph.add_node("interpret", self._interpret)
        graph.add_node("decide", self._decide)

        graph.add_edge(START, "classify_risk")
        graph.add_edge("classify_risk", "build_plan")
        graph.add_edge("build_plan", "enforce_floor")
        graph.add_edge("enforce_floor", "gather_evidence")
        graph.add_edge("gather_evidence", "interpret")
        graph.add_edge("interpret", "decide")
        graph.add_edge("decide", END)
        return graph.compile()

    async def evaluate(self, tx: TransactionRequest, mandate: Mandate) -> SupervisorState:
        """Run one transaction through the full flow."""
        final = await self._graph.ainvoke(SupervisorState(tx=tx, mandate=mandate))
        return SupervisorState.model_validate(final)

    # ------------------------------------------------------------------ nodes
    async def _classify_risk(self, state: SupervisorState) -> dict[str, Any]:
        started = time.perf_counter()
        baseline = self.policy.baseline_tier(state.tx, state.mandate)
        result = await self.brains.think(
            instructions=RISK_INSTRUCTIONS,
            prompt=(
                f"Transaction: {state.tx.amount} {state.tx.currency} to beneficiary "
                f"{state.tx.beneficiary_id} "
                f"({'NEW beneficiary' if state.tx.beneficiary_is_new else 'known beneficiary'}). "
                f"Mandate limit: {state.mandate.scope.amount_limit} "
                f"{state.mandate.scope.currency} per {state.mandate.scope.period}. "
                f"Mandate status: {state.mandate.status.value}. "
                f"Channel: {state.tx.channel or 'agent-initiated'}."
            ),
            output_type=RiskAssessment,
            heuristic=RiskAssessment(
                risk_tier=baseline,
                rationale="Deterministic baseline from amount, beneficiary and mandate status.",
                factors=[
                    f"amount={state.tx.amount}",
                    f"new_beneficiary={state.tx.beneficiary_is_new}",
                ],
            ),
        )
        assessment: RiskAssessment = result.output  # type: ignore[assignment]

        # The agent's tier is recorded as proposed; policy raises it to the
        # baseline in enforce_floor. Both are kept so the demo can show the two.
        return self._traced(
            state,
            TraceStep(
                step="classify_risk",
                summary=f"Risk classified {assessment.risk_tier.value.upper()}",
                detail={
                    "agent_tier": assessment.risk_tier.value,
                    "policy_baseline": baseline.value,
                    "rationale": assessment.rationale,
                    "factors": assessment.factors,
                },
                brain=result.brain,
                degraded=result.degraded,
                latency_ms=int((time.perf_counter() - started) * 1000),
            ),
            agent_tier=assessment.risk_tier,
            risk_tier=self.policy.effective_tier(assessment.risk_tier, state.tx, state.mandate),
        )

    async def _build_plan(self, state: SupervisorState) -> dict[str, Any]:
        started = time.perf_counter()
        floor = self.policy.floor_signals(state.risk_tier)
        result = await self.brains.think(
            instructions=PLAN_INSTRUCTIONS,
            prompt=(
                f"Risk tier: {state.risk_tier.value}. "
                f"Amount {state.tx.amount} {state.tx.currency}, "
                f"beneficiary {'NEW' if state.tx.beneficiary_is_new else 'known'}. "
                "Choose the signals to verify."
            ),
            output_type=PlanProposal,
            heuristic=PlanProposal(
                signals=sorted(floor, key=lambda s: s.value),
                rationale="Deterministic fallback: the policy floor for this tier.",
            ),
        )
        proposal: PlanProposal = result.output  # type: ignore[assignment]

        # Binding and identity are proved once, at mandate creation: Number
        # Verification needs a 3-legged consent token, and KYC Match compares a
        # claimed identity that does not change per transaction. Filtered here so
        # a model cannot pull issuance-time checks into the hot path.
        signals = [s for s in proposal.signals if s not in ISSUANCE_ONLY_SIGNALS]
        plan = VerificationPlan(
            risk_tier=state.risk_tier, signals=signals, rationale=proposal.rationale
        )
        return self._traced(
            state,
            TraceStep(
                step="build_plan",
                summary=f"Agent planned {len(signals)} checks",
                detail={
                    "signals": [s.value for s in signals],
                    "rationale": proposal.rationale,
                },
                brain=result.brain,
                degraded=result.degraded,
                latency_ms=int((time.perf_counter() - started) * 1000),
            ),
            plan=plan,
        )

    async def _enforce_floor(self, state: SupervisorState) -> dict[str, Any]:
        """Deterministic node: the agent may add checks, never remove them."""
        assert state.plan is not None
        before = set(state.plan.signals)
        enforced = self.policy.enforce_plan(state.plan, state.risk_tier)
        added = [s.value for s in enforced.signals if s not in before]

        return self._traced(
            state,
            TraceStep(
                step="enforce_floor",
                summary=(
                    f"Policy floor added {len(added)} check(s)"
                    if added
                    else "Agent plan already meets the policy floor"
                ),
                detail={
                    "effective_tier": state.risk_tier.value,
                    "added_by_policy": added,
                    "final_plan": [s.value for s in enforced.signals],
                },
            ),
            plan=enforced,
        )

    async def _gather_evidence(self, state: SupervisorState) -> dict[str, Any]:
        assert state.plan is not None
        started = time.perf_counter()
        params = self.policy.freshness_params(state.risk_tier)
        bundle = await self.nac.fetch_many(
            state.plan.signals,
            state.mandate.principal_msisdn,
            claimed_name=state.mandate.principal_id,
            **params,
        )
        usable = bundle.usable_signals()
        return self._traced(
            state,
            TraceStep(
                step="gather_evidence",
                summary=f"{len(usable)}/{len(state.plan.signals)} signals returned",
                detail={
                    "results": {
                        s.value: (r.result if r.is_usable else {"error": r.error_code})
                        for s, r in bundle.records.items()
                    },
                    "dimensions_covered": sorted(d.value for d in bundle.covered_dimensions()),
                    "freshness": params,
                },
                latency_ms=int((time.perf_counter() - started) * 1000),
            ),
            evidence=bundle,
        )

    async def _interpret(self, state: SupervisorState) -> dict[str, Any]:
        started = time.perf_counter()
        summary = {
            s.value: (r.result if r.is_usable else {"unavailable": r.error_code})
            for s, r in state.evidence.records.items()
        }
        alarming = self._alarming(state.evidence)
        result = await self.brains.think(
            instructions=INTERPRET_INSTRUCTIONS,
            prompt=(
                f"Transaction: {state.tx.amount} {state.tx.currency} to "
                f"{'a NEW' if state.tx.beneficiary_is_new else 'a known'} beneficiary. "
                f"Risk tier: {state.risk_tier.value}.\n"
                f"Signals: {summary}"
            ),
            output_type=EvidenceInterpretation,
            heuristic=EvidenceInterpretation(
                proposed_verdict=Verdict.STEP_UP if alarming else Verdict.ALLOW,
                rationale="Deterministic fallback over the gathered signals.",
                concerns=alarming,
            ),
        )
        interpretation: EvidenceInterpretation = result.output  # type: ignore[assignment]
        return self._traced(
            state,
            TraceStep(
                step="interpret",
                summary=f"Agent proposes {interpretation.proposed_verdict.value.upper()}",
                detail={
                    "rationale": interpretation.rationale,
                    "concerns": interpretation.concerns,
                },
                brain=result.brain,
                degraded=result.degraded,
                latency_ms=int((time.perf_counter() - started) * 1000),
            ),
            agent_proposal=interpretation.proposed_verdict,
            agent_rationale=interpretation.rationale,
        )

    async def _decide(self, state: SupervisorState) -> dict[str, Any]:
        """Deterministic node: the policy engine owns the outcome."""
        decision = self.policy.decide(
            state.tx,
            state.mandate,
            state.evidence,
            agent_tier=state.agent_tier,
            agent_proposal=state.agent_proposal,
            agent_rationale=state.agent_rationale,
        )
        overridden = (
            state.agent_proposal is not None and state.agent_proposal is not decision.verdict
        )
        return self._traced(
            state,
            TraceStep(
                step="decide",
                summary=(
                    f"POLICY {decision.verdict.value.upper()}"
                    + (
                        f" (overrode agent {state.agent_proposal.value.upper()})"
                        if overridden and state.agent_proposal
                        else ""
                    )
                ),
                detail={
                    "verdict": decision.verdict.value,
                    "agent_proposal": state.agent_proposal.value if state.agent_proposal else None,
                    "policy_overrode_agent": overridden,
                    "reason_codes": decision.reason_codes,
                    "policy_version": decision.policy_version,
                },
            ),
            decision=decision,
        )

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _alarming(evidence: EvidenceBundle) -> list[str]:
        """Deterministic reading of 'something here is worrying'."""
        flags = {
            Signal.SIM_SWAP: "swapped",
            Signal.DEVICE_SWAP: "swapped",
            Signal.CALL_FORWARDING: "forwarding_active",
            Signal.NUMBER_RECYCLING: "recycled",
        }
        found = []
        for signal, key in flags.items():
            record = evidence.get(signal)
            if record and record.is_usable and record.result.get(key):
                found.append(signal.value)
        if any(not r.is_usable for r in evidence.records.values()):
            found.append("unavailable_signals")
        return found

    def _traced(self, state: SupervisorState, step: TraceStep, **updates: Any) -> dict[str, Any]:
        if self.on_trace is not None:
            # The UI must never be able to break a decision.
            with contextlib.suppress(Exception):
                self.on_trace(step)
        return {"trace": [*state.trace, step], **updates}


__all__ = ["CORE_SPINE", "SupervisorState", "WakalahSupervisor"]
