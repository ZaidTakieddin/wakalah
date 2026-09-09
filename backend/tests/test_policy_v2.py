"""Rules v2 tests: deterministic friction for new-beneficiary payments.

v2 exists because two demo beats depended on the LLM being generous (docs/09
D29). These tests pin the guarantee that replaced that hope:

    * a first material payment to a NEW beneficiary always steps up —
      whatever the agent proposes;
    * paying someone new also requires usable continuity proof (the number was
      not reassigned) — missing proof is absence of evidence, never a pass;
    * known beneficiaries and small amounts are untouched;
    * v1 semantics are frozen — the same facts under v1 do NOT fire v2 rules.
"""

from __future__ import annotations

from typing import Any

import pytest

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
)
from app.policy.engine import PolicyEngine

MSISDN = "+99999991001"


@pytest.fixture(scope="module")
def v2() -> PolicyEngine:
    return PolicyEngine("v2")


@pytest.fixture(scope="module")
def v1() -> PolicyEngine:
    return PolicyEngine("v1")


def make_mandate(**overrides: Any) -> Mandate:
    defaults: dict[str, Any] = {
        "mandate_id": "man_1",
        "principal_id": "hash_amina",
        "principal_msisdn": MSISDN,
        "agent_id": "agent_rasheed",
        "agent_key_fingerprint": "fp_abc",
        # Like the demo story: the landlord is permitted but has never been paid.
        "scope": MandateScope(amount_limit=2000, beneficiary_ids=["ben_mother", "ben_landlord"]),
    }
    return Mandate(**{**defaults, **overrides})


def make_tx(amount: float, beneficiary_is_new: bool, **overrides: Any) -> TransactionRequest:
    defaults: dict[str, Any] = {
        "transaction_id": "tx_v2",
        "mandate_id": "man_1",
        "amount": amount,
        "beneficiary_id": "ben_landlord" if beneficiary_is_new else "ben_mother",
        "beneficiary_is_new": beneficiary_is_new,
    }
    return TransactionRequest(**{**defaults, **overrides})


def evidence(**signals: dict[str, Any]) -> EvidenceBundle:
    bundle = EvidenceBundle()
    for name, result in signals.items():
        signal = Signal(name)
        bundle.add(
            EvidenceRecord(
                signal=signal,
                dimension=SIGNAL_DIMENSION[signal],
                subject={"phoneNumber": MSISDN},
                result=result,
                source=EvidenceSource.LIVE,
            )
        )
    return bundle


def clean_floor(**extra: dict[str, Any]) -> EvidenceBundle:
    base: dict[str, dict[str, Any]] = {
        "sim_swap": {"swapped": False},
        "device_swap": {"swapped": False},
        "call_forwarding": {"forwarding_active": False},
        "number_recycling": {"recycled": False},
        "reachability": {"reachable": True},
    }
    base.update(extra)
    return evidence(**base)


class TestNewBeneficiaryFriction:
    def test_material_first_payment_steps_up(self, v2: PolicyEngine) -> None:
        decision = v2.decide(make_tx(1500, True), make_mandate(), clean_floor())
        assert decision.verdict is Verdict.STEP_UP
        assert "NEW_BENEFICIARY_MATERIAL_VALUE" in decision.reason_codes
        assert decision.policy_version == "v2"

    @pytest.mark.parametrize("amount", [499.99, 500])
    def test_threshold_boundary(self, v2: PolicyEngine, amount: float) -> None:
        decision = v2.decide(make_tx(amount, True), make_mandate(), clean_floor())
        assert ("NEW_BENEFICIARY_MATERIAL_VALUE" in decision.reason_codes) is (amount >= 500)

    def test_known_beneficiary_is_unaffected(self, v2: PolicyEngine) -> None:
        decision = v2.decide(make_tx(1500, False), make_mandate(), clean_floor())
        assert decision.verdict is Verdict.ALLOW
        assert "NEW_BENEFICIARY_MATERIAL_VALUE" not in decision.reason_codes

    def test_small_first_payment_is_unaffected(self, v2: PolicyEngine) -> None:
        decision = v2.decide(make_tx(150, True), make_mandate(), clean_floor())
        # 150 to a new beneficiary: medium tier by baseline, but no friction rule.
        assert decision.verdict is Verdict.ALLOW


class TestContinuityCoverage:
    def test_missing_continuity_proof_never_allows_a_new_beneficiary(
        self, v2: PolicyEngine
    ) -> None:
        """The takeover class this rule exists for: recycled number + new payee."""
        thin = evidence(
            sim_swap={"swapped": False},
            device_swap={"swapped": False},
            call_forwarding={"forwarding_active": False},
            reachability={"reachable": True},
            number_recycling={},
        )
        # Make recycling genuinely unusable (an operator outage answer).
        record = thin.records[Signal.NUMBER_RECYCLING]
        thin.records[Signal.NUMBER_RECYCLING] = record.model_copy(
            update={"ok": False, "source": EvidenceSource.UNAVAILABLE, "error_code": "OUTAGE"}
        )

        decision = v2.decide(make_tx(600, True), make_mandate(), thin)

        assert decision.verdict is Verdict.STEP_UP
        assert "INSUFFICIENT_EVIDENCE" in decision.reason_codes

    def test_recycled_number_on_new_beneficiary_denies(self, v2: PolicyEngine) -> None:
        decision = v2.decide(
            make_tx(600, True),
            make_mandate(),
            clean_floor(number_recycling={"recycled": True}),
        )
        assert decision.verdict is Verdict.DENY
        assert "NUMBER_RECYCLED" in decision.reason_codes

    def test_plan_floor_pulls_recycling_for_new_beneficiaries(self, v2: PolicyEngine) -> None:
        plan_signals_low = v2.floor_signals(RiskTier.LOW, beneficiary_is_new=True)
        plan_signals_known = v2.floor_signals(RiskTier.LOW, beneficiary_is_new=False)
        assert Signal.NUMBER_RECYCLING in plan_signals_low
        assert Signal.NUMBER_RECYCLING not in plan_signals_known


class TestClonedAgentBeat:
    def test_hijack_and_continuity_codes_land_together(self, v2: PolicyEngine) -> None:
        """The documented cloned-agent beat: hijack AND continuity codes."""
        compromised = clean_floor(
            sim_swap={"swapped": True},
            device_swap={"swapped": True},
            call_forwarding={"forwarding_active": True},
            number_recycling={"recycled": True},
        )
        decision = v2.decide(make_tx(1800, True), make_mandate(), compromised)

        assert decision.verdict is Verdict.DENY
        for code in (
            "SIM_SWAP_RECENT_HIGH_VALUE",
            "NUMBER_RECYCLED",
            "DEVICE_SWAP_RECENT",
            "CALL_FORWARDING_ACTIVE",
        ):
            assert code in decision.reason_codes


class TestV1IsFrozen:
    def test_v1_does_not_fire_v2_rules(self, v1: PolicyEngine) -> None:
        """Released rules never change in place; old verdicts stay reproducible."""
        decision = v1.decide(make_tx(1500, True), make_mandate(), clean_floor())
        assert decision.verdict is Verdict.ALLOW
        assert decision.policy_version == "v1"
