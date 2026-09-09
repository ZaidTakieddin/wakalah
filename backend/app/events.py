"""In-process event bus: how the demo sees inside a decision as it happens.

NacClient and the supervisor publish; WebSocket clients subscribe. Neither
producer knows a UI exists, which keeps the live API panel and the reasoning
trace from leaking into the decision path.

Four rules:
    * publishing never blocks a decision — a slow or dead subscriber is dropped
      from its own queue, not allowed to stall a payment verification;
    * every event is a typed schema (app/models/events.py) rendered to the wire
      as JSON {type, ts, payload} — one schema feeds both this stream and the
      audit trail (CLAUDE.md invariant 4);
    * an event type without a registered schema raises here, at publish time,
      instead of leaking an undocumented shape onto the stream;
    * every event carries its correlation IDs — anything emitted inside a
      scenario beat gains `beatId`, anything inside an evaluation gains
      `transactionId` — attached here from ambient scopes, so producers never
      thread context through their signatures.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections import deque
from collections.abc import Iterator
from contextvars import ContextVar
from typing import Any

from app.models.domain import utc_now
from app.models.events import PAYLOAD_MODELS, encode_payload

MAX_QUEUE = 256
REPLAY_BUFFER = 200
"""Recent events kept so a client connecting mid-run still sees the story."""

_current_beat: ContextVar[str | None] = ContextVar("wakalah_beat", default=None)
_current_transaction: ContextVar[str | None] = ContextVar("wakalah_tx", default=None)


@contextlib.contextmanager
def beat_scope(beat_id: str) -> Iterator[None]:
    """Mark everything published inside as belonging to one scenario beat."""
    token = _current_beat.set(beat_id)
    try:
        yield
    finally:
        _current_beat.reset(token)


@contextlib.contextmanager
def transaction_scope(transaction_id: str) -> Iterator[None]:
    """Mark everything published inside as belonging to one evaluation."""
    token = _current_transaction.set(transaction_id)
    try:
        yield
    finally:
        _current_transaction.reset(token)


def current_beat_id() -> str | None:
    return _current_beat.get()


def current_transaction_id() -> str | None:
    return _current_transaction.get()


class EventBus:
    """Fan-out pub/sub with a small replay buffer."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._recent: deque[dict[str, Any]] = deque(maxlen=REPLAY_BUFFER)

    # ---------------------------------------------------------------- publish
    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Validate, serialize and fan out an event.

        Ambient correlation IDs are attached first: a `beatId` when inside a
        scenario beat, a `transactionId` when inside an evaluation — but only
        onto schemas that declare them, and never over an explicit value the
        producer set itself. Absent scope means absent keys, never nulls.

        Safe to call from sync code and from any task.
        """
        enriched = dict(payload)
        model = PAYLOAD_MODELS.get(event_type)
        if model is not None:
            fields = model.model_fields
            # Correlation fills gaps only: strip explicit nulls on the two id
            # keys first (decision.final arrives as a full dump carrying
            # beatId: null, which must not shadow a real ambient id via alias
            # precedence), then fill whatever is still missing from scope.
            for key in ("beat_id", "beatId", "transaction_id", "transactionId"):
                if enriched.get(key) is None:
                    enriched.pop(key, None)
            beat_id = _current_beat.get()
            if beat_id is not None and "beat_id" in fields:
                enriched.setdefault("beat_id", beat_id)
            transaction_id = _current_transaction.get()
            if transaction_id is not None and "transaction_id" in fields:
                enriched.setdefault("transaction_id", transaction_id)
        wire = encode_payload(event_type, enriched)
        # Correlation ids are absent — never null — outside their scope. Every
        # other null (brain, challenge, errorCode) is contract and stays.
        for key in ("beatId", "transactionId"):
            if wire.get(key) is None:
                wire.pop(key, None)
        event = {
            "type": event_type,
            "ts": utc_now().isoformat(),
            "payload": wire,
        }
        self._recent.append(event)

        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # A subscriber that cannot keep up loses events rather than
                # slowing the decision down.
                with contextlib.suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
                with contextlib.suppress(asyncio.QueueFull):
                    queue.put_nowait(event)

    # -------------------------------------------------------------- subscribe
    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=MAX_QUEUE)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    def recent(self) -> list[dict[str, Any]]:
        return list(self._recent)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


bus = EventBus()
"""The process-wide bus. One backend, one demo, one stream."""
