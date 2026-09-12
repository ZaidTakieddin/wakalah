"""Store tests: id generation and the in-memory repositories."""

from __future__ import annotations

import re
from typing import Any

from app.models.domain import Decision, Mandate, MandateScope, MandateStatus, RiskTier, Verdict
from app.store.memory import DecisionStore, MandateStore, next_id


def test_next_id_is_ordered_readable_and_unpredictable() -> None:
    first, second = next_id("man"), next_id("man")

    assert re.fullmatch(r"man_\d{4}_[0-9a-f]{8}", first)
    # Counter increases (debuggable order), randomness differs (unguessable).
    assert int(second.split("_")[1]) == int(first.split("_")[1]) + 1
    assert first != second


def make_mandate(mandate_id: str = "man_1", **overrides: Any) -> Mandate:
    defaults: dict[str, Any] = {
        "mandate_id": mandate_id,
        "principal_id": "hash_amina",
        "principal_msisdn": "+99999991001",
        "agent_id": "agent_rasheed",
        "agent_key_fingerprint": "fp_abc",
        "scope": MandateScope(amount_limit=2000, beneficiary_ids=["ben_mother"]),
    }
    return Mandate(**{**defaults, **overrides})


class TestMandateStore:
    def test_put_get_round_trip(self) -> None:
        store = MandateStore()
        assert store.get("missing") is None
        store.put(make_mandate())
        assert store.get("man_1") is not None

    def test_set_status_revokes_with_reason(self) -> None:
        store = MandateStore()
        store.put(make_mandate())
        assert store.set_status("missing", MandateStatus.REVOKED) is None

        updated = store.set_status("man_1", MandateStatus.REVOKED, "sim_swap_detected")
        assert updated is not None
        assert updated.status is MandateStatus.REVOKED
        assert updated.revoked_reason == "sim_swap_detected"

    def test_for_msisdn_filters(self) -> None:
        store = MandateStore()
        store.put(make_mandate("man_1", principal_msisdn="+99999991001"))
        store.put(make_mandate("man_2", principal_msisdn="+99999991000"))

        assert [m.mandate_id for m in store.for_msisdn("+99999991001")] == ["man_1"]


class TestDecisionStore:
    def test_put_get_round_trip(self) -> None:
        store = DecisionStore()
        decision = Decision(transaction_id="tx_1", verdict=Verdict.ALLOW, risk_tier=RiskTier.LOW)
        assert store.get("tx_1") is None
        store.put(decision)
        assert store.get("tx_1") is decision
