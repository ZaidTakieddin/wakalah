"""Run the three demo beats end-to-end against the live sandbox.

    .venv\\Scripts\\python.exe -m scripts.demo_scenarios

Beat 1  LOW     Amina's routine remittance          -> expect ALLOW
Beat 2  HIGH    cloned agent after a SIM swap       -> expect DENY, plan expands
Beat 3  MEDIUM  operator signals unavailable        -> expect STEP_UP, degraded

The point of beat 2 is not just the verdict: watch the plan grow between beat 1
and beat 2. That difference is the agent deciding, which is what the rubric
scores under "Agentic AI & Multi-API Orchestration".
"""

from __future__ import annotations

import asyncio

from app.agents.schemas import TraceStep
from app.agents.supervisor import WakalahSupervisor
from app.models.domain import Mandate, MandateScope, TransactionRequest
from app.nac.client import NacClient

CLEAN = "+99999991001"
COMPROMISED = "+99999991000"
UNAVAILABLE = "+99999990503"


def mandate_for(msisdn: str, **overrides) -> Mandate:
    defaults = {
        "mandate_id": "man_amina_001",
        "principal_id": "Amina Haddad",
        "principal_msisdn": msisdn,
        "agent_id": "agent_rasheed",
        "agent_key_fingerprint": "fp_rasheed_ed25519",
        "scope": MandateScope(amount_limit=2000, beneficiary_ids=["ben_mother"]),
    }
    return Mandate(**{**defaults, **overrides})


def print_trace(step: TraceStep) -> None:
    brain = f" [{step.brain}{'*degraded' if step.degraded else ''}]" if step.brain else ""
    took = f" {step.latency_ms}ms" if step.latency_ms else ""
    print(f"   . {step.step:<16}{brain}{took}  {step.summary}")


async def run_beat(title: str, msisdn: str, tx: TransactionRequest, **mandate_kw) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    async with NacClient() as nac:
        supervisor = WakalahSupervisor(nac=nac, on_trace=print_trace)
        state = await supervisor.evaluate(tx, mandate_for(msisdn, **mandate_kw))

    decision = state.decision
    assert decision is not None
    plan = state.plan.signals if state.plan else []
    print(f"\n   agent tier      : {state.agent_tier.value}")
    print(f"   effective tier  : {decision.risk_tier.value}")
    print(f"   plan ({len(plan)})       : {', '.join(s.value for s in plan)}")
    print(f"   agent proposed  : {state.agent_proposal.value if state.agent_proposal else '-'}")
    print(f"   POLICY VERDICT  : {decision.verdict.value.upper()}")
    print(f"   reason codes    : {decision.reason_codes or ['-']}")
    print(f"   rationale       : {decision.rationale[:160]}")


async def main() -> None:
    await run_beat(
        "BEAT 1  Amina's routine monthly remittance (clean principal)",
        CLEAN,
        TransactionRequest(
            transaction_id="tx_beat1",
            mandate_id="man_amina_001",
            amount=150.0,
            beneficiary_id="ben_mother",
        ),
    )

    await run_beat(
        "BEAT 2  Cloned agent, new beneficiary, hijacked principal",
        COMPROMISED,
        TransactionRequest(
            transaction_id="tx_beat2",
            mandate_id="man_amina_001",
            amount=1800.0,
            beneficiary_id="ben_mother",
            beneficiary_is_new=True,
        ),
    )

    await run_beat(
        "BEAT 3  Operator signals unavailable (graceful degradation)",
        UNAVAILABLE,
        TransactionRequest(
            transaction_id="tx_beat3",
            mandate_id="man_amina_001",
            amount=600.0,
            beneficiary_id="ben_mother",
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
