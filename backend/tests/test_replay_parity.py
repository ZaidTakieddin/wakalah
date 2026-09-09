"""Replay parity tests (backend/CLAUDE.md §Tests).

The replay cache is the demo's fallback when the network is dead, so it must
behave *identically* to a live call:

    1. Every recorded file, run through NacClient's replay path, normalizes to
       exactly what the live path would have produced from that same body.
    2. The policy engine must reach the same verdict from replay-labelled
       evidence as from live-labelled evidence — provenance labels honesty,
       they never change decisions.
    3. The one deliberate asymmetry: Number Verification stays gated behind
       the 3-legged consent token even in replay (issuance-only by design).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from app.models.domain import (
    SIGNAL_DIMENSION,
    Decision,
    EvidenceBundle,
    EvidenceRecord,
    EvidenceSource,
    Mandate,
    MandateScope,
    Signal,
    TransactionRequest,
)
from app.nac.client import NacClient
from app.nac.endpoints import SPECS
from app.policy.engine import PolicyEngine

REPLAY_DIR = Path(__file__).resolve().parent.parent / "replay_cache"
CLEAN = "+99999991001"
COMPROMISED = "+99999991000"

CASES = sorted(REPLAY_DIR.glob("*.json"))
assert CASES, "replay cache is empty — parity suite has nothing to prove"


# ----------------------------------------------------------------- helpers
def make_mandate(**overrides: Any) -> Mandate:
    defaults: dict[str, Any] = {
        "mandate_id": "man_1",
        "principal_id": "hash_amina",
        "principal_msisdn": CLEAN,
        "agent_id": "agent_rasheed",
        "agent_key_fingerprint": "fp_abc",
        "scope": MandateScope(amount_limit=2000, beneficiary_ids=["ben_mother"]),
    }
    return Mandate(**{**defaults, **overrides})


def make_tx(amount: float, beneficiary_is_new: bool) -> TransactionRequest:
    return TransactionRequest(
        transaction_id="tx_parity",
        mandate_id="man_1",
        amount=amount,
        beneficiary_id="ben_mother",
        beneficiary_is_new=beneficiary_is_new,
    )


def bundle_from(records: list[EvidenceRecord]) -> EvidenceBundle:
    bundle = EvidenceBundle()
    for record in records:
        bundle.add(record)
    return bundle


def relabel(bundle: EvidenceBundle, source: EvidenceSource) -> EvidenceBundle:
    """Same facts, different provenance label."""
    twin = EvidenceBundle()
    for _signal, record in bundle.records.items():
        twin.add(
            record.model_copy(
                update={
                    "source": source,
                    "evidence_time": record.evidence_time,
                }
            )
        )
    return twin


async def fetch_replay(signal: Signal, msisdn: str) -> EvidenceRecord:
    async with NacClient(mode="replay", record=False) as client:
        return await client.fetch(signal, msisdn)


# ------------------------------------------------------- file-level parity
@pytest.mark.parametrize("path", CASES, ids=[p.name for p in CASES])
def test_replayed_response_matches_live_normalization(path: Path) -> None:
    stem = path.stem
    signal_value, msisdn = stem.split("__", 1)
    signal = Signal(signal_value)

    raw = json.loads(path.read_text(encoding="utf-8"))

    record = asyncio.run(fetch_replay(signal, msisdn))

    assert record.source is EvidenceSource.REPLAY
    assert record.is_usable, f"{stem} replays as unusable evidence"
    assert record.result == SPECS[signal].normalize(raw)
    assert record.dimension is SIGNAL_DIMENSION[signal]
    assert record.subject == {"phoneNumber": msisdn}


def test_every_cached_signal_is_in_the_spec_map() -> None:
    cached = {p.stem.split("__", 1)[0] for p in CASES}
    spec_names = {s.value for s in SPECS}
    assert cached <= spec_names


# ------------------------------------------------------------ policy parity
@pytest.mark.parametrize(
    ("msisdn", "amount", "beneficiary_is_new"),
    [
        (CLEAN, 150, False),  # routine beat
        (CLEAN, 1500, True),  # step-up beat
        (COMPROMISED, 1800, True),  # cloned-agent beat
    ],
    ids=["routine", "stepup", "cloned_agent"],
)
def test_policy_decides_identically_on_live_and_replay_evidence(
    msisdn: str, amount: float, beneficiary_is_new: bool
) -> None:
    signals = [s for s in SPECS if s is not Signal.NUMBER_VERIFICATION]

    async def gather() -> EvidenceBundle:
        async with NacClient(mode="replay", record=False) as client:
            return await client.fetch_many(signals, msisdn)

    replayed = asyncio.run(gather())
    as_live = relabel(replayed, EvidenceSource.LIVE)

    engine = PolicyEngine()
    mandate = make_mandate(principal_msisdn=msisdn)

    from_replay: Decision = engine.decide(make_tx(amount, beneficiary_is_new), mandate, replayed)
    from_live: Decision = engine.decide(make_tx(amount, beneficiary_is_new), mandate, as_live)

    assert from_replay.verdict is from_live.verdict
    assert from_replay.reason_codes == from_live.reason_codes
    assert from_replay.risk_tier is from_live.risk_tier

    # Sanity on the story itself: the compromised persona must deny.
    if msisdn == COMPROMISED:
        assert from_replay.verdict.value == "deny"


# ------------------------------------------------------------- bearer gating
def test_number_verification_stays_consent_gated_even_in_replay() -> None:
    record = asyncio.run(fetch_replay(Signal.NUMBER_VERIFICATION, CLEAN))

    assert not record.is_usable
    assert record.error_code == "CONSENT_TOKEN_REQUIRED"
    assert record.result == {}
