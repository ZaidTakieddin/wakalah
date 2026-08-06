"""The audit trail: every decision and the evidence that justified it.

Writes to Supabase when it is configured and reachable, and degrades to the
in-memory store otherwise. That fallback is not a shortcut — a demo must not
die because a database is unreachable, and a verification must never fail
because we could not write a log line. Persistence failures are reported, never
raised into the decision path.

Privacy: the audit tables are keyed by `principal_ref`, a SHA-256 hash of the
phone number. The long-lived tables hold no raw subscriber identifiers.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

from app.config import settings
from app.models.domain import Decision, Mandate

logger = logging.getLogger(__name__)


def principal_ref(msisdn: str) -> str:
    """Stable pseudonymous key for a subscriber. One-way by design."""
    return hashlib.sha256(msisdn.encode("utf-8")).hexdigest()[:32]


class AuditTrail:
    """Persists mandates, decisions and evidence."""

    def __init__(self) -> None:
        self._client: Any | None = None
        self._enabled = bool(settings.supabase_url and settings.supabase_service_key)
        self._failed = False
        self.last_error: str | None = None

    @property
    def backend(self) -> str:
        if not self._enabled:
            return "memory (supabase not configured)"
        if self._failed:
            return f"memory (supabase unavailable: {self.last_error})"
        return "supabase"

    def _get_client(self) -> Any | None:
        if not self._enabled or self._failed:
            return None
        if self._client is None:
            try:
                from supabase import create_client

                self._client = create_client(settings.supabase_url, settings.supabase_service_key)
            except Exception as exc:  # any import/connect failure degrades
                self._mark_failed(exc)
                return None
        return self._client

    def _mark_failed(self, exc: Exception) -> None:
        self._failed = True
        self.last_error = f"{type(exc).__name__}: {exc}"[:200]
        logger.warning("audit trail falling back to memory - %s", self.last_error)

    # ------------------------------------------------------------------ write
    async def record_mandate(self, mandate: Mandate) -> None:
        client = self._get_client()
        if client is None:
            return
        row = {
            "mandate_id": mandate.mandate_id,
            "principal_ref": principal_ref(mandate.principal_msisdn),
            "principal_id": mandate.principal_id,
            "principal_msisdn": mandate.principal_msisdn,
            "agent_id": mandate.agent_id,
            "agent_key_fingerprint": mandate.agent_key_fingerprint,
            "scope": mandate.scope.model_dump(mode="json"),
            "status": mandate.status.value,
            "policy_version": mandate.policy_version,
            "revoked_reason": mandate.revoked_reason,
            "created_at": mandate.created_at.isoformat(),
            "expires_at": mandate.expires_at.isoformat() if mandate.expires_at else None,
        }
        await self._write(lambda: client.table("mandates").upsert(row).execute())

    async def record_decision(self, decision: Decision, mandate: Mandate) -> None:
        client = self._get_client()
        if client is None:
            return
        ref = principal_ref(mandate.principal_msisdn)
        overrode = (
            decision.agent_proposal is not None and decision.agent_proposal is not decision.verdict
        )
        decision_row = {
            "transaction_id": decision.transaction_id,
            "mandate_id": mandate.mandate_id,
            "principal_ref": ref,
            "verdict": decision.verdict.value,
            "risk_tier": decision.risk_tier.value,
            "agent_proposal": (decision.agent_proposal.value if decision.agent_proposal else None),
            "policy_overrode": overrode,
            "reason_codes": decision.reason_codes,
            "rationale": decision.rationale,
            "policy_version": decision.policy_version,
            "latency_ms": decision.latency_ms,
            "decided_at": decision.decided_at.isoformat(),
        }
        evidence_rows = [
            {
                "transaction_id": decision.transaction_id,
                "signal": signal.value,
                "dimension": record.dimension.value,
                "provider": record.provider,
                "result": record.result,
                "source": record.source.value,
                "purpose": record.purpose,
                "legal_basis": record.legal_basis,
                "consent_status": record.consent_status.value,
                "ok": record.ok,
                "error_code": record.error_code,
                "latency_ms": record.latency_ms,
                "evidence_time": record.evidence_time.isoformat(),
            }
            for signal, record in decision.evidence.records.items()
        ]

        def write() -> None:
            client.table("decisions").upsert(decision_row).execute()
            if evidence_rows:
                client.table("decision_evidence").insert(evidence_rows).execute()

        await self._write(write)

    async def _write(self, operation: Any) -> None:
        """Run a blocking Supabase call off the event loop; never raise."""
        try:
            await asyncio.to_thread(operation)
        except Exception as exc:  # a log write must not break a verification
            self._mark_failed(exc)

    # ------------------------------------------------------------------- read
    async def history_for(self, msisdn: str, limit: int = 20) -> list[dict[str, Any]]:
        """Recent decisions for a principal — the compliance-officer view."""
        client = self._get_client()
        if client is None:
            return []
        ref = principal_ref(msisdn)

        def read() -> list[dict[str, Any]]:
            response = (
                client.table("decisions")
                .select("*")
                .eq("principal_ref", ref)
                .order("decided_at", desc=True)
                .limit(limit)
                .execute()
            )
            return list(response.data or [])

        try:
            return await asyncio.to_thread(read)
        except Exception as exc:
            self._mark_failed(exc)
            return []


audit = AuditTrail()
