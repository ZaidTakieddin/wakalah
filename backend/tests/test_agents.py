"""Agent contract tests (backend/CLAUDE.md §Tests).

The rule: test the *contract*, never the LLM's prose. So every brain here is a
stub, and what gets asserted are the typed boundaries that keep an AI from
breaking the system:

    * agents answer in typed schemas or not at all;
    * the supervisor filters issuance-only signals out of transaction plans,
      no matter what the model asks for;
    * policy floors survive any agent plan;
    * the graph runs its six steps in order and reports each one;
    * a dead brain degrades honestly instead of lying.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from pydantic import ValidationError

from app.agents.brains import BrainResult, BrainRouter
from app.agents.schemas import (
    EvidenceInterpretation,
    PlanProposal,
    RiskAssessment,
    TraceStep,
)
from app.agents.supervisor import SupervisorState, WakalahSupervisor
from app.config import settings
from app.models.domain import (
    SIGNAL_DIMENSION,
    EvidenceBundle,
    EvidenceRecord,
    EvidenceSource,
    Mandate,
    MandateScope,
    RiskTier,
    Signal,
    TransactionRequest,
    Verdict,
    VerificationPlan,
)
from tests.conftest import HeuristicOnlyBrains

MSISDN = "+99999991001"


# ------------------------------------------------------------------ helpers
def make_mandate(**overrides: Any) -> Mandate:
    defaults: dict[str, Any] = {
        "mandate_id": "man_1",
        "principal_id": "hash_amina",
        "principal_msisdn": MSISDN,
        "agent_id": "agent_rasheed",
        "agent_key_fingerprint": "fp_abc",
        "scope": MandateScope(amount_limit=2000, beneficiary_ids=["ben_mother"]),
    }
    return Mandate(**{**defaults, **overrides})


def make_tx(**overrides: Any) -> TransactionRequest:
    defaults: dict[str, Any] = {
        "transaction_id": "tx_1",
        "mandate_id": "man_1",
        "amount": 1500.0,
        "beneficiary_id": "ben_landlord",
        "beneficiary_is_new": True,
    }
    return TransactionRequest(**{**defaults, **overrides})


class FakeNac:
    """Duck-typed NacClient: returns pre-built evidence, records what was asked."""

    def __init__(self, results: dict[Signal, dict[str, Any]] | None = None) -> None:
        self._results = results or {}
        self.requested: list[list[Signal]] = []

    async def fetch_many(
        self, signals: Any, msisdn: str, *, access_token: str | None = None, **params: Any
    ) -> EvidenceBundle:
        wanted = list(signals)
        self.requested.append(wanted)
        bundle = EvidenceBundle()
        for signal in wanted:
            result = self._results.get(signal)
            if result is None:
                bundle.add(
                    EvidenceRecord(
                        signal=signal,
                        dimension=SIGNAL_DIMENSION[signal],
                        subject={"phoneNumber": msisdn},
                        result={},
                        source=EvidenceSource.UNAVAILABLE,
                        ok=False,
                        error_code="NOT_STUBBED",
                    )
                )
            else:
                bundle.add(
                    EvidenceRecord(
                        signal=signal,
                        dimension=SIGNAL_DIMENSION[signal],
                        subject={"phoneNumber": msisdn},
                        result=result,
                        source=EvidenceSource.LIVE,
                    )
                )
        return bundle


COMPROMISED_RESULTS: dict[Signal, dict[str, Any]] = {
    Signal.SIM_SWAP: {"swapped": True},
    Signal.DEVICE_SWAP: {"swapped": True},
    Signal.CALL_FORWARDING: {"forwarding_active": True},
    Signal.NUMBER_RECYCLING: {"recycled": True},
    Signal.REACHABILITY: {"reachable": True},
}


# ------------------------------------------------------------ schema contracts
class TestSchemas:
    def test_plan_proposal_rejects_unknown_signal_names(self) -> None:
        with pytest.raises(ValidationError):
            PlanProposal(signals=["not_a_signal"], rationale="x")

    def test_risk_assessment_factors_default_empty(self) -> None:
        assessment = RiskAssessment(risk_tier=RiskTier.LOW, rationale="fine")
        assert assessment.factors == []

    def test_interpretation_requires_a_verdict(self) -> None:
        with pytest.raises(ValidationError):
            EvidenceInterpretation(proposed_verdict="maybe", rationale="x")

    def test_trace_step_defaults(self) -> None:
        step = TraceStep(step="decide", summary="done")
        assert step.brain is None
        assert step.degraded is False
        assert step.latency_ms is None


# --------------------------------------------------------- supervisor contract
class GreedyPlanner(HeuristicOnlyBrains):
    """A misbehaving agent: plans everything, including issuance-time checks."""

    async def think(
        self,
        *,
        instructions: str,
        prompt: str,
        output_type: Any,
        heuristic: Any,
    ) -> BrainResult:
        if output_type is PlanProposal:
            return BrainResult(
                output=PlanProposal(
                    signals=[
                        Signal.NUMBER_VERIFICATION,
                        Signal.KYC_MATCH,
                        Signal.SIM_SWAP,
                    ],
                    rationale="the agent wants every check it can get",
                ),
                brain="stub",
            )
        return await super().think(
            instructions=instructions, prompt=prompt, output_type=output_type, heuristic=heuristic
        )


class TestSupervisorNodes:
    def test_build_plan_filters_issuance_only_signals(self) -> None:
        """Binding/identity checks belong to mandate creation; no model may
        pull them into the per-transaction hot path."""
        supervisor = WakalahSupervisor(nac=FakeNac(), brains=GreedyPlanner())
        state = SupervisorState(tx=make_tx(), mandate=make_mandate(), risk_tier=RiskTier.LOW)

        result = asyncio.run(supervisor._build_plan(state))
        planned = {s for s in result["plan"].signals}

        assert planned == {Signal.SIM_SWAP}
        assert Signal.NUMBER_VERIFICATION not in planned
        assert Signal.KYC_MATCH not in planned

    def test_enforce_floor_adds_back_whatever_the_agent_dropped(self) -> None:
        supervisor = WakalahSupervisor(nac=FakeNac(), brains=HeuristicOnlyBrains())
        thin = VerificationPlan(risk_tier=RiskTier.HIGH, signals=[Signal.SIM_SWAP])
        state = SupervisorState(
            tx=make_tx(), mandate=make_mandate(), risk_tier=RiskTier.HIGH, plan=thin
        )

        result = asyncio.run(supervisor._enforce_floor(state))

        detail = result["trace"][-1].detail
        assert detail["added_by_policy"], "policy floor failed to fire"
        assert set(detail["final_plan"]) >= {
            Signal.SIM_SWAP,
            Signal.DEVICE_SWAP,
            Signal.CALL_FORWARDING,
            Signal.NUMBER_RECYCLING,
            Signal.REACHABILITY,
        }

    def test_full_graph_runs_the_six_canonical_steps_in_order(self) -> None:
        seen: list[TraceStep] = []
        supervisor = WakalahSupervisor(
            nac=FakeNac(COMPROMISED_RESULTS),
            brains=HeuristicOnlyBrains(),
            on_trace=seen.append,
        )

        final = asyncio.run(supervisor.evaluate(make_tx(amount=1800), make_mandate()))

        assert [step.step for step in final.trace] == [
            "classify_risk",
            "build_plan",
            "enforce_floor",
            "gather_evidence",
            "interpret",
            "decide",
        ]
        # Every step was also streamed to the UI hook as it happened.
        assert [step.step for step in seen] == [step.step for step in final.trace]

        assert final.decision is not None
        assert final.decision.verdict is Verdict.DENY
        assert "SIM_SWAP_RECENT_HIGH_VALUE" in final.decision.reason_codes

    def test_exploding_ui_hook_never_breaks_the_decision(self) -> None:
        def hostile_hook(step: TraceStep) -> None:
            raise RuntimeError("the dashboard is down")

        supervisor = WakalahSupervisor(
            nac=FakeNac(COMPROMISED_RESULTS),
            brains=HeuristicOnlyBrains(),
            on_trace=hostile_hook,
        )

        final = asyncio.run(supervisor.evaluate(make_tx(amount=1800), make_mandate()))

        assert len(final.trace) == 6
        assert final.decision is not None
        assert final.decision.verdict is Verdict.DENY


# -------------------------------------------------------------- brain fallback
class TestBrainRouter:
    def test_all_brains_dead_degrades_to_heuristic_honestly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "gemini_api_key", "")
        monkeypatch.setattr(settings, "groq_api_key", "")

        router = BrainRouter()
        router._dead["ollama"] = "prefailed: offline"
        assert router.available() == []

        heuristic = RiskAssessment(risk_tier=RiskTier.LOW, rationale="rules")
        result = asyncio.run(
            router.think(
                instructions="i", prompt="p", output_type=RiskAssessment, heuristic=heuristic
            )
        )

        assert result.brain == "heuristic"
        assert result.degraded is True
        assert result.output is heuristic
        assert "prefailed" in (result.error or "")

    @pytest.mark.parametrize(
        ("exc", "expected"),
        [
            (type("E", (Exception,), {})("denied"), False),
            (type("HttpError", (Exception,), {"status_code": 403})("forbidden"), True),
            (Exception("invalid api key supplied"), True),
            (type("Timeout", (Exception,), {})("timed out"), False),
        ],
        ids=["plain-error", "http-403", "bad-key", "timeout"],
    )
    def test_permanent_vs_temporary_brain_failures(self, exc: Exception, expected: bool) -> None:
        assert BrainRouter._is_permanent(exc) is expected
