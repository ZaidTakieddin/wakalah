"""Policy engine tests.

The policy layer is where money decisions are made, so it is tested as a table
of cases rather than a happy path. Every test states the security property it
protects, not just the expected value.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from app.models.domain import (
    SIGNAL_DIMENSION,
    EvidenceBundle,
    EvidenceRecord,
    EvidenceSource,
    Mandate,
    MandateScope,
    MandateStatus,
    RiskTier,
    Signal,
    TransactionRequest,
    Verdict,
    VerificationPlan,
    utc_now,
)
from app.policy.engine import PolicyEngine

MSISDN = "+99999991001"


@pytest.fixture
def engine() -> PolicyEngine:
    return PolicyEngine("v1")


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
        "amount": 100.0,
        "beneficiary_id": "ben_mother",
    }
    return TransactionRequest(**{**defaults, **overrides})


def evidence(**signals: dict[str, Any]) -> EvidenceBundle:
    """Build a bundle: evidence(sim_swap={"swapped": True})."""
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


def clean_floor(tier: RiskTier = RiskTier.LOW, **extra: dict[str, Any]) -> EvidenceBundle:
    """Evidence that satisfies the floor for a tier with nothing alarming."""
    base: dict[str, dict[str, Any]] = {
        "sim_swap": {"swapped": False},
        "device_swap": {"swapped": False},
        "call_forwarding": {"forwarding_active": False},
        "number_recycling": {"recycled": False},
        "reachability": {"reachable": True},
    }
    base.update(extra)
    return evidence(**base)


# ------------------------------------------------------------------ tiering
class TestRiskTiering:
    """The agent may raise risk; hard facts stop it lowering risk."""

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [(100, RiskTier.LOW), (500, RiskTier.MEDIUM), (2000, RiskTier.HIGH)],
    )
    def test_amount_sets_baseline(self, engine, amount, expected):
        assert engine.baseline_tier(make_tx(amount=amount), make_mandate()) is expected

    def test_new_beneficiary_raises_baseline(self, engine):
        tx = make_tx(amount=10, beneficiary_is_new=True)
        assert engine.baseline_tier(tx, make_mandate()) is RiskTier.MEDIUM

    def test_challenge_only_principal_is_high_risk(self, engine):
        mandate = make_mandate(status=MandateStatus.CHALLENGE_ONLY)
        assert engine.baseline_tier(make_tx(), mandate) is RiskTier.HIGH

    def test_agent_can_escalate(self, engine):
        tier = engine.effective_tier(RiskTier.HIGH, make_tx(amount=10), make_mandate())
        assert tier is RiskTier.HIGH

    def test_agent_cannot_downgrade_below_baseline(self, engine):
        """The core protection: a mis-classification cannot under-check."""
        tx = make_tx(amount=5000)
        tier = engine.effective_tier(RiskTier.LOW, tx, make_mandate())
        assert tier is RiskTier.HIGH


# -------------------------------------------------------------- plan floors
class TestPlanFloor:
    def test_missing_floor_signals_are_added_back(self, engine):
        plan = VerificationPlan(risk_tier=RiskTier.HIGH, signals=[Signal.SIM_SWAP])
        enforced = engine.enforce_plan(plan, RiskTier.HIGH)
        assert engine.floor_signals(RiskTier.HIGH) <= set(enforced.signals)
        assert "policy floor added" in enforced.rationale

    def test_agent_extras_are_preserved(self, engine):
        plan = VerificationPlan(risk_tier=RiskTier.LOW, signals=[Signal.SIM_SWAP, Signal.ROAMING])
        assert Signal.ROAMING in engine.enforce_plan(plan, RiskTier.LOW).signals

    def test_higher_tier_asks_a_stricter_question(self, engine):
        low = engine.freshness_params(RiskTier.LOW)["max_age_hours"]
        high = engine.freshness_params(RiskTier.HIGH)["max_age_hours"]
        assert high < low


# ---------------------------------------------------------------- verdicts
class TestVerdicts:
    def test_clean_transaction_is_allowed(self, engine):
        decision = engine.decide(make_tx(), make_mandate(), clean_floor())
        assert decision.verdict is Verdict.ALLOW
        assert decision.reason_codes == []

    def test_sim_swap_with_material_amount_is_denied(self, engine):
        bundle = clean_floor(sim_swap={"swapped": True})
        decision = engine.decide(make_tx(amount=1500), make_mandate(), bundle)
        assert decision.verdict is Verdict.DENY
        assert "SIM_SWAP_RECENT_HIGH_VALUE" in decision.reason_codes

    def test_sim_swap_with_trivial_amount_challenges(self, engine):
        bundle = clean_floor(sim_swap={"swapped": True})
        decision = engine.decide(make_tx(amount=50), make_mandate(), bundle)
        assert decision.verdict is Verdict.STEP_UP

    def test_device_swap_alone_challenges_never_denies(self, engine):
        """People buy phones. A new handset is a question, not an accusation."""
        bundle = clean_floor(device_swap={"swapped": True})
        decision = engine.decide(make_tx(amount=1500), make_mandate(), bundle)
        assert decision.verdict is Verdict.STEP_UP
        assert "DEVICE_SWAP_RECENT" in decision.reason_codes

    def test_recycled_number_is_denied(self, engine):
        bundle = clean_floor(number_recycling={"recycled": True})
        decision = engine.decide(make_tx(), make_mandate(), bundle)
        assert decision.verdict is Verdict.DENY

    def test_identity_mismatch_is_denied(self, engine):
        bundle = clean_floor(kyc_match={"attributes": {"nameMatch": "false"}, "any_mismatch": True})
        decision = engine.decide(make_tx(), make_mandate(), bundle)
        assert decision.verdict is Verdict.DENY
        assert "IDENTITY_MISMATCH" in decision.reason_codes

    def test_call_forwarding_challenges(self, engine):
        bundle = clean_floor(call_forwarding={"forwarding_active": True})
        assert engine.decide(make_tx(), make_mandate(), bundle).verdict is Verdict.STEP_UP


class TestMandateRules:
    def test_revoked_mandate_is_denied(self, engine):
        mandate = make_mandate(status=MandateStatus.REVOKED, revoked_reason="sim_swap")
        decision = engine.decide(make_tx(), mandate, clean_floor())
        assert decision.verdict is Verdict.DENY
        assert "MANDATE_NOT_ACTIVE" in decision.reason_codes

    def test_expired_mandate_is_denied(self, engine):
        mandate = make_mandate(expires_at=utc_now() - timedelta(hours=1))
        assert engine.decide(make_tx(), mandate, clean_floor()).verdict is Verdict.DENY

    def test_amount_over_scope_is_denied(self, engine):
        decision = engine.decide(make_tx(amount=9999), make_mandate(), clean_floor())
        assert "AMOUNT_EXCEEDS_MANDATE_LIMIT" in decision.reason_codes

    def test_unlisted_beneficiary_is_denied(self, engine):
        decision = engine.decide(
            make_tx(beneficiary_id="ben_attacker"), make_mandate(), clean_floor()
        )
        assert "BENEFICIARY_NOT_PERMITTED" in decision.reason_codes

    def test_challenge_only_principal_gets_step_up(self, engine):
        mandate = make_mandate(status=MandateStatus.CHALLENGE_ONLY)
        bundle = clean_floor(tenure={"tenure_confirmed": True})
        decision = engine.decide(make_tx(), mandate, bundle)
        assert decision.verdict is Verdict.STEP_UP
        assert "PRINCIPAL_CHALLENGE_ONLY" in decision.reason_codes


class TestEvidenceCoverage:
    def test_thin_evidence_never_allows(self, engine):
        """An outage or rate limit must degrade to a challenge, not a pass."""
        decision = engine.decide(make_tx(), make_mandate(), EvidenceBundle())
        assert decision.verdict is Verdict.STEP_UP
        assert "INSUFFICIENT_EVIDENCE" in decision.reason_codes

    def test_failed_signal_is_not_treated_as_clean(self, engine):
        bundle = EvidenceBundle()
        bundle.add(
            EvidenceRecord(
                signal=Signal.SIM_SWAP,
                dimension=SIGNAL_DIMENSION[Signal.SIM_SWAP],
                result={},
                source=EvidenceSource.UNAVAILABLE,
                ok=False,
                error_code="HTTP_503",
            )
        )
        decision = engine.decide(make_tx(), make_mandate(), bundle)
        assert decision.verdict is Verdict.STEP_UP


class TestContext:
    def test_roaming_explains_an_out_of_area_device(self, engine):
        """A genuinely travelling customer should not be punished for travelling."""
        bundle = clean_floor(
            location_verification={"in_expected_area": False},
            roaming={"roaming": True, "country": "TR"},
        )
        assert engine.decide(make_tx(amount=1500), make_mandate(), bundle).verdict is (
            Verdict.ALLOW
        )

    def test_out_of_area_without_roaming_challenges(self, engine):
        bundle = clean_floor(
            location_verification={"in_expected_area": False},
            roaming={"roaming": False},
        )
        decision = engine.decide(make_tx(amount=1500), make_mandate(), bundle)
        assert decision.verdict is Verdict.STEP_UP
        assert "LOCATION_INCONSISTENT" in decision.reason_codes


class TestDeterminism:
    def test_same_inputs_produce_the_same_decision(self, engine):
        """The property that makes a verdict auditable months later."""
        tx, mandate, bundle = (
            make_tx(amount=1500),
            make_mandate(),
            clean_floor(sim_swap={"swapped": True}),
        )
        now = utc_now()
        first = engine.decide(tx, mandate, bundle, now=now)
        second = engine.decide(tx, mandate, bundle, now=now)
        assert first.verdict is second.verdict
        assert first.reason_codes == second.reason_codes
        assert first.rationale == second.rationale

    def test_decision_records_the_policy_version(self, engine):
        assert engine.decide(make_tx(), make_mandate(), clean_floor()).policy_version == ("v1")

    def test_agent_proposal_is_preserved_beside_the_verdict(self, engine):
        """'AI proposes, policy disposes' has to be visible, not just claimed."""
        bundle = clean_floor(sim_swap={"swapped": True})
        decision = engine.decide(
            make_tx(amount=1500),
            make_mandate(),
            bundle,
            agent_proposal=Verdict.ALLOW,
        )
        assert decision.agent_proposal is Verdict.ALLOW
        assert decision.verdict is Verdict.DENY
