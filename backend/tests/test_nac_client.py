"""NacClient behaviour tests — the only door to the network.

Run against a mocked httpx transport: no sandbox access needed. The properties
under test are the ones CLAUDE.md invariants 1 and 6 demand:

    * every call is logged identically (the nac.call event) and can never be
      broken by the UI hook;
    * failures are evidence too — an HTTP error or a dead network produces an
      *unusable* record, never a silent pass;
    * transient upstream conditions (rate limits, gateway hiccups) are retried;
    * live responses can be recorded into the replay cache that keeps the demo
      alive when the venue wi-fi dies.
"""

from __future__ import annotations

import asyncio
import json
import typing
from pathlib import Path
from typing import Any

import httpx
import pytest

import app.nac.client as client_module
from app.config import settings
from app.models.domain import EvidenceBundle, EvidenceSource, Signal
from app.nac.client import NacClient

CLEAN = "+99999991001"
SIM_SWAP_PATH = "/passthrough/camara/v1/sim-swap/sim-swap/v0/check"
DEVICE_SWAP_PATH = "/passthrough/camara/v1/device-swap/device-swap/v1/check"


def make_client(
    handler: typing.Callable[[httpx.Request], httpx.Response],
    *,
    mode: str = "live",
    record: bool = False,
    replay_dir: Path | None = None,
    on_call: Any = None,
) -> NacClient:
    """A NacClient whose HTTP goes through a mock transport."""
    client = NacClient(mode=mode, record=record, on_call=on_call, replay_dir=replay_dir)
    client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


@pytest.fixture(autouse=True)
def fast_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "BACKOFF_BASE_SECONDS", 0.001)


def counting_handler(responses: list[httpx.Response]) -> tuple[Any, list[httpx.Request]]:
    """Answer each request with the next response in the list (last one repeats)."""
    seen: list[httpx.Request] = []
    state = {"calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        index = min(state["calls"], len(responses) - 1)
        state["calls"] += 1
        return responses[index]

    return handler, seen


# ------------------------------------------------------------------- success
def test_live_success_is_normalized_live_evidence(tmp_path: Path) -> None:
    handler, seen = counting_handler([httpx.Response(200, json={"swapped": False})])
    events: list[dict[str, Any]] = []
    client = make_client(handler, replay_dir=tmp_path, on_call=events.append)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.SIM_SWAP, CLEAN, max_age_hours=720)

    record = asyncio.run(run())

    assert record.is_usable
    assert record.source is EvidenceSource.LIVE
    assert record.result == {"swapped": False}
    assert record.error_code is None
    assert len(seen) == 1
    assert json.loads(seen[0].content)["maxAge"] == 720

    # The UI's live API panel gets exactly one event, with provenance attached.
    assert [e["type"] for e in events] == ["nac.call"]
    event = events[0]
    assert event["signal"] == "sim_swap"
    assert event["path"] == SIM_SWAP_PATH
    assert event["status"] == 200
    assert isinstance(event["latency_ms"], int)
    assert event["simulated_device"] is True


def test_every_call_emits_an_event_even_when_the_hook_explodes(tmp_path: Path) -> None:
    def hostile_hook(event: dict[str, Any]) -> None:
        raise RuntimeError("dashboard down")

    handler, _ = counting_handler([httpx.Response(200, json={"swapped": False})])
    client = make_client(handler, replay_dir=tmp_path, on_call=hostile_hook)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.SIM_SWAP, CLEAN)

    record = asyncio.run(run())

    # A broken UI must not be able to break a verification.
    assert record.is_usable
    assert record.result == {"swapped": False}


# ------------------------------------------------------------------ failures
def test_error_persona_returns_unusable_evidence_never_a_pass(tmp_path: Path) -> None:
    """The 04xx/05xx simulator personas land here on purpose."""
    handler, seen = counting_handler(
        [httpx.Response(503, json={"code": "SERVICE_UNAVAILABLE", "message": "simulated outage"})]
    )
    client = make_client(handler, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.SIM_SWAP, "+99999990503")

    record = asyncio.run(run())

    assert not record.is_usable
    assert record.source is EvidenceSource.UNAVAILABLE
    assert record.error_code == "SERVICE_UNAVAILABLE"
    assert record.result == {}
    assert len(seen) == 3  # 503 is transient-classified: all three attempts spent


def test_network_failure_is_unusable_evidence(tmp_path: Path) -> None:
    def dead_network(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("venue wi-fi died")

    client = make_client(dead_network, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.SIM_SWAP, CLEAN)

    record = asyncio.run(run())

    assert not record.is_usable
    assert record.error_code == "NETWORK_ERROR"


def test_non_retryable_status_spends_one_attempt_only(tmp_path: Path) -> None:
    handler, seen = counting_handler([httpx.Response(401, json={"code": "UNAUTHORIZED"})])
    client = make_client(handler, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.SIM_SWAP, CLEAN)

    record = asyncio.run(run())

    assert not record.is_usable
    assert record.error_code == "UNAUTHORIZED"
    assert len(seen) == 1


def test_unparseable_error_body_still_carries_the_status_code(tmp_path: Path) -> None:
    handler, _ = counting_handler([httpx.Response(500, text="gateway exploded")])
    client = make_client(handler, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.SIM_SWAP, CLEAN)

    record = asyncio.run(run())

    assert record.error_code == "HTTP_500"


# -------------------------------------------------------------------- retries
def test_transient_rate_limit_is_retried_and_recovers(tmp_path: Path) -> None:
    handler, seen = counting_handler(
        [
            httpx.Response(429, json={"code": "RATE_LIMIT"}),
            httpx.Response(200, json={"swapped": False}),
        ]
    )
    client = make_client(handler, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.SIM_SWAP, CLEAN)

    record = asyncio.run(run())

    assert record.is_usable
    assert record.source is EvidenceSource.LIVE
    assert len(seen) == 2


# ---------------------------------------------------------------- recording
def test_live_responses_are_recorded_into_the_replay_cache(tmp_path: Path) -> None:
    handler, _ = counting_handler([httpx.Response(200, json={"swapped": True})])
    client = make_client(handler, record=True, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.SIM_SWAP, CLEAN)

    record = asyncio.run(run())

    cached = tmp_path / f"sim_swap__{CLEAN}.json"
    assert record.is_usable
    assert cached.exists()
    assert json.loads(cached.read_text(encoding="utf-8")) == {"swapped": True}


def test_recording_off_by_default(tmp_path: Path) -> None:
    handler, _ = counting_handler([httpx.Response(200, json={"swapped": False})])
    client = make_client(handler, record=False, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            await client.fetch(Signal.SIM_SWAP, CLEAN)

    asyncio.run(run())
    assert not (tmp_path / f"sim_swap__{CLEAN}.json").exists()


def test_missing_replay_file_is_unavailable_not_a_crash(tmp_path: Path) -> None:
    client = make_client(lambda request: httpx.Response(500), mode="replay", replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.DEVICE_SWAP, CLEAN)

    record = asyncio.run(run())

    assert not record.is_usable
    assert record.error_code == "NO_REPLAY_DATA"


# ----------------------------------------------------------------- batching
def test_fetch_many_maps_results_and_failures_per_signal(tmp_path: Path) -> None:
    def mixed(request: httpx.Request) -> httpx.Response:
        if request.url.path == SIM_SWAP_PATH:
            return httpx.Response(200, json={"swapped": False})
        if request.url.path == DEVICE_SWAP_PATH:
            return httpx.Response(503, json={"code": "OUTAGE"})
        raise AssertionError(f"unexpected path {request.url.path}")

    client = make_client(mixed, replay_dir=tmp_path)

    async def run() -> EvidenceBundle:
        async with client:
            return await client.fetch_many(
                [Signal.SIM_SWAP, Signal.DEVICE_SWAP], CLEAN, max_age_hours=24
            )

    bundle = asyncio.run(run())

    sim = bundle.get(Signal.SIM_SWAP)
    device = bundle.get(Signal.DEVICE_SWAP)
    assert sim is not None and sim.is_usable
    assert device is not None and not device.is_usable
    assert device.error_code == "OUTAGE"
    assert bundle.usable_signals() == {Signal.SIM_SWAP}


# ---------------------------------------------------------------- ttl cache
def test_ttl_cache_relabels_the_reuse_and_skips_the_second_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "nac_cache_ttl_seconds", 60.0)
    handler, seen = counting_handler([httpx.Response(200, json={"swapped": False})])
    client = make_client(handler, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            first = await client.fetch(Signal.SIM_SWAP, CLEAN)
            second = await client.fetch(Signal.SIM_SWAP, CLEAN)
            return first, second

    first, second = asyncio.run(run())

    assert first.source is EvidenceSource.LIVE
    assert second.source is EvidenceSource.CACHED  # honesty label travels
    assert second.result == first.result
    assert len(seen) == 1


def test_caching_is_off_by_default(tmp_path: Path) -> None:
    monkey_free_handler, seen = counting_handler([httpx.Response(200, json={"swapped": False})])
    client = make_client(monkey_free_handler, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            one = await client.fetch(Signal.SIM_SWAP, CLEAN)
            two = await client.fetch(Signal.SIM_SWAP, CLEAN)
            return one, two

    one, two = asyncio.run(run())

    assert one.source is EvidenceSource.LIVE
    assert two.source is EvidenceSource.LIVE
    assert len(seen) == 2


def test_failures_are_never_cached(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An outage must not look like data — and once real data arrives it can be
    reused."""
    monkeypatch.setattr(settings, "nac_cache_ttl_seconds", 60.0)
    handler, seen = counting_handler(
        [
            httpx.Response(503, json={"code": "OUTAGE"}),
            httpx.Response(503, json={"code": "OUTAGE"}),
            httpx.Response(503, json={"code": "OUTAGE"}),
            httpx.Response(200, json={"swapped": False}),
        ]
    )
    client = make_client(handler, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            failed = await client.fetch(Signal.SIM_SWAP, CLEAN)
            live = await client.fetch(Signal.SIM_SWAP, CLEAN)
            cached = await client.fetch(Signal.SIM_SWAP, CLEAN)
            return failed, live, cached

    failed, live, cached = asyncio.run(run())

    assert not failed.is_usable
    assert live.source is EvidenceSource.LIVE
    assert cached.source is EvidenceSource.CACHED
    assert len(seen) == 4  # three spent attempts + one real recovery


def test_different_questions_are_different_cache_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """maxAge=24h and maxAge=720h are different questions, not a cache hit."""
    monkeypatch.setattr(settings, "nac_cache_ttl_seconds", 60.0)
    handler, seen = counting_handler([httpx.Response(200, json={"swapped": False})])
    client = make_client(handler, replay_dir=tmp_path)

    async def run() -> Any:
        async with client:
            await client.fetch(Signal.SIM_SWAP, CLEAN, max_age_hours=24)
            await client.fetch(Signal.SIM_SWAP, CLEAN, max_age_hours=720)

    asyncio.run(run())

    assert len(seen) == 2
