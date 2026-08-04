"""The deterministic policy engine — final authority on every verdict.

Three guarantees this module must keep (backend/CLAUDE.md invariant 3):

    * no LLM, no randomness, no wall clock  -> the same facts and rules always
      produce the same decision, which is what makes a verdict auditable;
    * the agent may escalate above the floor, never plan below it;
    * a missing signal is absence of evidence, never a pass.

The rules themselves live in rules_v1.yaml so they can be read and versioned
without reading Python.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from app.models.domain import (
    Decision,
    EvidenceBundle,
    Mandate,
    MandateStatus,
    RiskTier,
    Signal,
    TransactionRequest,
    Verdict,
    VerificationPlan,
    utc_now,
)

RULES_DIR = Path(__file__).resolve().parent

TIER_ORDER: dict[RiskTier, int] = {RiskTier.LOW: 0, RiskTier.MEDIUM: 1, RiskTier.HIGH: 2}


def _max_tier(*tiers: RiskTier) -> RiskTier:
    return max(tiers, key=lambda t: TIER_ORDER[t])


@dataclass(frozen=True)
class PolicyOutcome:
    """A single rule firing."""

    verdict: Verdict
    reason_code: str
    detail: str = ""


class PolicyEngine:
    """Loads a versioned rule set and applies it."""

    def __init__(self, version: str = "v1") -> None:
        self.version = version
        path = RULES_DIR / f"rules_{version}.yaml"
        self.rules: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------- risk tiering
    def baseline_tier(self, tx: TransactionRequest, mandate: Mandate) -> RiskTier:
        """The lowest tier this transaction may be treated as.

        This is the real closure of the "what if the AI under-classifies?" hole:
        the floor is per-tier, so a mis-classified tier would drag the floor down
        with it. Hard facts — amount, a new beneficiary, a principal already under
        challenge-only mode — set a deterministic minimum the agent cannot go below.
        """
        cfg = self.rules["tiering"]
        tier = RiskTier.LOW

        if tx.amount >= float(cfg["high_amount"]):
            tier = _max_tier(tier, RiskTier.HIGH)
        elif tx.amount >= float(cfg["medium_amount"]):
            tier = _max_tier(tier, RiskTier.MEDIUM)

        if tx.beneficiary_is_new:
            tier = _max_tier(tier, RiskTier(cfg["new_beneficiary_min_tier"]))

        if mandate.status is MandateStatus.CHALLENGE_ONLY:
            tier = _max_tier(tier, RiskTier(cfg["challenge_only_min_tier"]))

        return tier

    def effective_tier(
        self, agent_tier: RiskTier, tx: TransactionRequest, mandate: Mandate
    ) -> RiskTier:
        """The agent may raise the tier; it can never lower it below the baseline."""
        return _max_tier(agent_tier, self.baseline_tier(tx, mandate))

    # ------------------------------------------------------------ plan floors
    def floor_signals(self, tier: RiskTier, phase: str = "transaction") -> set[Signal]:
        return {Signal(name) for name in self.rules["floors"][phase][tier.value]}

    def enforce_plan(
        self, plan: VerificationPlan, tier: RiskTier, phase: str = "transaction"
    ) -> VerificationPlan:
        """Return the agent's plan with any missing floor signals added back."""
        required = self.floor_signals(tier, phase)
        chosen = list(dict.fromkeys(plan.signals))
        missing = [s for s in sorted(required, key=lambda s: s.value) if s not in chosen]
        if not missing:
            return plan.model_copy(update={"risk_tier": tier})
        return plan.model_copy(
            update={
                "risk_tier": tier,
                "signals": chosen + missing,
                "rationale": (
                    f"{plan.rationale} | policy floor added: {', '.join(s.value for s in missing)}"
                ).strip(" |"),
            }
        )

    def freshness_params(self, tier: RiskTier) -> dict[str, int]:
        """Fetch parameters that tighten with risk (a stricter question, not just
        more questions)."""
        fresh = self.rules["freshness"]
        return {
            "max_age_hours": int(fresh["sim_swap_max_age_hours"][tier.value]),
            "device_swap_max_age_hours": int(fresh["device_swap_max_age_hours"][tier.value]),
        }

    # --------------------------------------------------------------- decision
    def decide(
        self,
        tx: TransactionRequest,
        mandate: Mandate,
        evidence: EvidenceBundle,
        *,
        agent_tier: RiskTier = RiskTier.LOW,
        agent_proposal: Verdict | None = None,
        agent_rationale: str = "",
        now: datetime | None = None,
    ) -> Decision:
        """Apply every rule and return the most severe outcome that fired."""
        now = now or utc_now()
        tier = self.effective_tier(agent_tier, tx, mandate)
        outcomes: list[PolicyOutcome] = []

        outcomes += self._mandate_rules(tx, mandate, now)
        outcomes += self._evidence_rules(tx, evidence)
        outcomes += self._coverage_rules(tier, evidence)

        verdict = self._most_severe(outcomes)
        return Decision(
            transaction_id=tx.transaction_id,
            verdict=verdict,
            risk_tier=tier,
            reason_codes=[o.reason_code for o in outcomes],
            rationale=self._rationale(verdict, outcomes, agent_rationale),
            agent_proposal=agent_proposal,
            policy_version=self.version,
            evidence=evidence,
            decided_at=now,
        )

    # ----------------------------------------------------------------- rules
    def _mandate_rules(
        self, tx: TransactionRequest, mandate: Mandate, now: datetime
    ) -> list[PolicyOutcome]:
        out: list[PolicyOutcome] = []

        if mandate.status is MandateStatus.REVOKED:
            out.append(
                PolicyOutcome(
                    Verdict.DENY, "MANDATE_NOT_ACTIVE", mandate.revoked_reason or "revoked"
                )
            )
        elif mandate.status is MandateStatus.EXPIRED or (
            mandate.expires_at is not None and mandate.expires_at <= now
        ):
            out.append(PolicyOutcome(Verdict.DENY, "MANDATE_NOT_ACTIVE", "expired"))
        elif mandate.status is MandateStatus.CHALLENGE_ONLY:
            out.append(
                PolicyOutcome(
                    Verdict.STEP_UP,
                    "PRINCIPAL_CHALLENGE_ONLY",
                    "principal is under challenge-only mode after a hijack signal",
                )
            )

        if tx.amount > mandate.scope.amount_limit:
            out.append(
                PolicyOutcome(
                    Verdict.DENY,
                    "AMOUNT_EXCEEDS_MANDATE_LIMIT",
                    f"{tx.amount} > {mandate.scope.amount_limit}",
                )
            )

        allowed = mandate.scope.beneficiary_ids
        if allowed and tx.beneficiary_id not in allowed:
            out.append(PolicyOutcome(Verdict.DENY, "BENEFICIARY_NOT_PERMITTED", tx.beneficiary_id))

        return out

    def _evidence_rules(
        self, tx: TransactionRequest, evidence: EvidenceBundle
    ) -> list[PolicyOutcome]:
        out: list[PolicyOutcome] = []
        thresholds = self.rules["thresholds"]

        def usable(signal: Signal) -> dict[str, Any] | None:
            record = evidence.get(signal)
            return record.result if record and record.is_usable else None

        if (kyc := usable(Signal.KYC_MATCH)) and kyc.get("any_mismatch"):
            out.append(PolicyOutcome(Verdict.DENY, "IDENTITY_MISMATCH", str(kyc.get("attributes"))))

        if (rec := usable(Signal.NUMBER_RECYCLING)) and rec.get("recycled"):
            out.append(
                PolicyOutcome(
                    Verdict.DENY,
                    "NUMBER_RECYCLED",
                    "the subscriber behind this number changed",
                )
            )

        if (swap := usable(Signal.SIM_SWAP)) and swap.get("swapped"):
            if tx.amount >= float(thresholds["swap_deny_amount"]):
                out.append(
                    PolicyOutcome(
                        Verdict.DENY,
                        "SIM_SWAP_RECENT_HIGH_VALUE",
                        f"recent SIM swap with amount {tx.amount}",
                    )
                )
            else:
                out.append(PolicyOutcome(Verdict.STEP_UP, "SIM_SWAP_RECENT_LOW_VALUE", ""))

        if (dev := usable(Signal.DEVICE_SWAP)) and dev.get("swapped"):
            # Alone this is weak — people buy phones. It challenges, never denies.
            out.append(PolicyOutcome(Verdict.STEP_UP, "DEVICE_SWAP_RECENT", ""))

        if (fwd := usable(Signal.CALL_FORWARDING)) and fwd.get("forwarding_active"):
            out.append(
                PolicyOutcome(
                    Verdict.STEP_UP,
                    "CALL_FORWARDING_ACTIVE",
                    "possible OTP/voice interception",
                )
            )

        if (nv := usable(Signal.NUMBER_VERIFICATION)) and not nv.get("number_verified"):
            out.append(PolicyOutcome(Verdict.STEP_UP, "NUMBER_NOT_VERIFIED", ""))

        if (reach := usable(Signal.REACHABILITY)) and not reach.get("reachable"):
            out.append(PolicyOutcome(Verdict.STEP_UP, "DEVICE_UNREACHABLE", ""))

        loc = usable(Signal.LOCATION_VERIFICATION)
        roaming = usable(Signal.ROAMING) or {}
        if (
            loc
            and not loc.get("in_expected_area")
            and tx.amount >= float(thresholds["location_check_amount"])
            and not roaming.get("roaming")
        ):
            # Roaming is context that explains an out-of-area device: a genuinely
            # travelling customer should not be punished for travelling.
            out.append(
                PolicyOutcome(
                    Verdict.STEP_UP,
                    "LOCATION_INCONSISTENT",
                    "device outside expected area and not roaming",
                )
            )

        return out

    def _coverage_rules(self, tier: RiskTier, evidence: EvidenceBundle) -> list[PolicyOutcome]:
        """Refuse to approve on thin evidence.

        If the floor could not be satisfied — an operator outage, a rate limit,
        an unsupported market — the safe answer is to challenge, never to allow.
        """
        required = self.floor_signals(tier)
        missing = sorted(required - evidence.usable_signals(), key=lambda s: s.value)
        if not missing:
            return []
        return [
            PolicyOutcome(
                Verdict.STEP_UP,
                "INSUFFICIENT_EVIDENCE",
                f"missing required signals: {', '.join(s.value for s in missing)}",
            )
        ]

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def _most_severe(outcomes: list[PolicyOutcome]) -> Verdict:
        if any(o.verdict is Verdict.DENY for o in outcomes):
            return Verdict.DENY
        if any(o.verdict is Verdict.STEP_UP for o in outcomes):
            return Verdict.STEP_UP
        return Verdict.ALLOW

    @staticmethod
    def _rationale(verdict: Verdict, outcomes: list[PolicyOutcome], agent_rationale: str) -> str:
        if not outcomes:
            base = "All required checks satisfied; no risk signals fired."
        else:
            base = "; ".join(
                f"{o.reason_code}{f' ({o.detail})' if o.detail else ''}"
                for o in outcomes
                if o.verdict is verdict
            )
        return f"{base} | agent: {agent_rationale}" if agent_rationale else base
