"""In-memory repositories.

Layer 6 swaps these for Supabase. Keeping them behind the same tiny interface
means the API layer never learns where state lives — the demo can run with no
database at all, which is one less thing to fail on stage.
"""

from __future__ import annotations

import itertools

from app.models.domain import Decision, Mandate, MandateStatus

_counter = itertools.count(1)


def next_id(prefix: str) -> str:
    return f"{prefix}_{next(_counter):04d}"


class MandateStore:
    def __init__(self) -> None:
        self._items: dict[str, Mandate] = {}

    def put(self, mandate: Mandate) -> Mandate:
        self._items[mandate.mandate_id] = mandate
        return mandate

    def get(self, mandate_id: str) -> Mandate | None:
        return self._items.get(mandate_id)

    def list(self) -> list[Mandate]:
        return list(self._items.values())

    def for_msisdn(self, msisdn: str) -> list[Mandate]:
        return [m for m in self._items.values() if m.principal_msisdn == msisdn]

    def set_status(
        self, mandate_id: str, status: MandateStatus, reason: str | None = None
    ) -> Mandate | None:
        mandate = self._items.get(mandate_id)
        if mandate is None:
            return None
        updated = mandate.model_copy(update={"status": status, "revoked_reason": reason})
        self._items[mandate_id] = updated
        return updated


class DecisionStore:
    def __init__(self) -> None:
        self._items: dict[str, Decision] = {}

    def put(self, decision: Decision) -> Decision:
        self._items[decision.transaction_id] = decision
        return decision

    def get(self, transaction_id: str) -> Decision | None:
        return self._items.get(transaction_id)

    def list(self) -> list[Decision]:
        return list(self._items.values())


mandates = MandateStore()
decisions = DecisionStore()
