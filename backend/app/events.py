"""In-process event bus: how the demo sees inside a decision as it happens.

NacClient and the supervisor publish; WebSocket clients subscribe. Neither
producer knows a UI exists, which keeps the live API panel and the reasoning
trace from leaking into the decision path.

Two rules:
    * publishing never blocks a decision — a slow or dead subscriber is dropped
      from its own queue, not allowed to stall a payment verification;
    * every event is a plain JSON-serialisable dict {type, ts, payload}.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections import deque
from typing import Any

from app.models.domain import utc_now

MAX_QUEUE = 256
REPLAY_BUFFER = 200
"""Recent events kept so a client connecting mid-run still sees the story."""


class EventBus:
    """Fan-out pub/sub with a small replay buffer."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._recent: deque[dict[str, Any]] = deque(maxlen=REPLAY_BUFFER)

    # ---------------------------------------------------------------- publish
    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event. Safe to call from sync code and from any task."""
        event = {
            "type": event_type,
            "ts": utc_now().isoformat(),
            "payload": payload,
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
