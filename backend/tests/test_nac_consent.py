"""Number Verification consent-flow tests (docs/02 D23 recipe, headless).

The whole 3-legged OAuth chain runs against a mocked transport: client
credentials -> discovery -> authorize redirect chain -> code -> token exchange
-> Bearer-authorized verify. No sandbox access needed.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest

import app.nac.client as client_module
from app.models.domain import EvidenceSource, Signal
from app.nac.client import NacClient
from app.nac.consent import ConsentTokenProvider

MSISDN = "+99999991001"
REDIRECT = "https://example.com/redirect"
NV_VERIFY_PATH = "/passthrough/camara/v1/number-verification/number-verification/v0/verify"


def consent_aware_handler(
    state: dict[str, int],
) -> Callable[[httpx.Request], Awaitable[httpx.Response]]:
    """A miniature Nokia sandbox: the exact endpoints the consent flow touches."""

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/oauth2/v1/auth/clientcredentials":
            state["client_credentials"] += 1
            return httpx.Response(200, json={"client_id": "cid_123", "client_secret": "sec_456"})
        if path == "/.well-known/openid-configuration":
            state["discovery"] += 1
            return httpx.Response(
                200,
                json={
                    "authorization_endpoint": "https://auth.example/oauth2/v1/authorize",
                    "token_endpoint": "https://auth.example/oauth2/v1/token",
                },
            )
        if path == "/oauth2/v1/authorize":
            state["authorize"] += 1
            if state["authorize"] % 3 != 0:
                # Nokia's own login/PKCE hops before ours, then it lands on the
                # redirect_uri carrying the code.
                return httpx.Response(302, headers={"location": str(request.url)})
            return httpx.Response(302, headers={"location": f"{REDIRECT}?code=abc123&state=xyz"})
        if path == "/oauth2/v1/token":
            state["token_exchange"] += 1
            form = parse_qs((await request.aread()).decode())
            assert form["grant_type"] == ["authorization_code"]
            assert form["code"] == ["abc123"]
            return httpx.Response(200, json={"access_token": "tok_789", "token_type": "Bearer"})
        if path == NV_VERIFY_PATH:
            state["verify"] += 1
            state["verify_auth"] = request.headers.get("authorization", "")
            return httpx.Response(200, json={"devicePhoneNumberVerified": True})
        raise AssertionError(f"unexpected endpoint: {path}")

    return handler


def make_client(handler: Callable[[httpx.Request], Any]) -> NacClient:
    """NacClient AND its consent provider share one mock transport â€” no real
    network anywhere."""
    transport = httpx.MockTransport(handler)
    client = NacClient(mode="live", record=False)
    client._http = httpx.AsyncClient(transport=transport)
    client.consent._http = httpx.AsyncClient(transport=transport)
    return client


@pytest.fixture(autouse=True)
def fast_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "BACKOFF_BASE_SECONDS", 0.001)


# ------------------------------------------------------------------ happy path
def test_full_consent_flow_mints_a_token_and_verifies() -> None:
    state: dict[str, int] = dict.fromkeys(
        ("client_credentials", "discovery", "authorize", "token_exchange", "verify"), 0
    )
    client = make_client(consent_aware_handler(state))

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.NUMBER_VERIFICATION, MSISDN)

    record = asyncio.run(run())

    assert record.is_usable
    assert record.source is EvidenceSource.LIVE
    assert record.result == {"number_verified": True}
    assert record.consent_status.value == "granted"
    assert state["verify"] == 1
    # The single-use token travelled as a Bearer header on the verify call only.
    assert state["verify_auth"] == "Bearer tok_789"


def test_consent_credentials_are_cached_per_process() -> None:
    state: dict[str, int] = dict.fromkeys(
        ("client_credentials", "discovery", "authorize", "token_exchange", "verify"), 0
    )
    client = make_client(consent_aware_handler(state))

    async def run() -> None:
        async with client:
            await client.fetch(Signal.NUMBER_VERIFICATION, MSISDN)
            await client.fetch(Signal.NUMBER_VERIFICATION, MSISDN)

    asyncio.run(run())

    assert state["client_credentials"] == 1
    assert state["discovery"] == 1
    assert state["authorize"] == 6  # fresh chain per token: they are single-use
    assert state["token_exchange"] == 2
    assert state["verify"] == 2


def test_explicit_access_token_skips_the_consent_flow() -> None:
    state: dict[str, int] = dict.fromkeys(
        ("client_credentials", "discovery", "authorize", "token_exchange", "verify"), 0
    )
    client = make_client(consent_aware_handler(state))

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.NUMBER_VERIFICATION, MSISDN, access_token="manual")

    record = asyncio.run(run())

    assert record.is_usable
    assert state["authorize"] == 0
    assert state["token_exchange"] == 0
    assert state["verify_auth"] == "Bearer manual"


# ---------------------------------------------------------------- degradation
@pytest.mark.parametrize(
    "break_at",
    ["client_credentials", "authorize_chain_never_lands"],
)
def test_consent_failure_degrades_to_unusable_evidence(break_at: str) -> None:
    def failing_handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if break_at == "client_credentials" and path.endswith("clientcredentials"):
            return httpx.Response(503, json={"code": "AUTH_DOWN"})
        if break_at == "authorize_chain_never_lands" and path == "/oauth2/v1/authorize":
            return httpx.Response(302, headers={"location": "https://auth.example/hop"})
        raise AssertionError("flow should have stopped before other endpoints")

    client = NacClient(mode="live", record=False)
    transport = httpx.MockTransport(failing_handler)
    client._http = httpx.AsyncClient(transport=transport)
    client.consent._http = httpx.AsyncClient(transport=transport)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.NUMBER_VERIFICATION, MSISDN)

    record = asyncio.run(run())

    assert not record.is_usable
    assert record.error_code == "CONSENT_TOKEN_REQUIRED"
    assert "unavailable right now" in (record.error_message or "")


def test_replay_mode_still_gates_number_verification(tmp_path: Path) -> None:
    """Offline demo: no token can be minted, so NV stays honestly unavailable."""
    calls: list[str] = []

    def never_called(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(500)

    client = NacClient(mode="replay", record=False, replay_dir=tmp_path)
    transport = httpx.MockTransport(never_called)
    client._http = httpx.AsyncClient(transport=transport)
    client.consent._http = httpx.AsyncClient(transport=transport)

    async def run() -> Any:
        async with client:
            return await client.fetch(Signal.NUMBER_VERIFICATION, MSISDN)

    record = asyncio.run(run())

    assert not record.is_usable
    assert record.error_code == "CONSENT_TOKEN_REQUIRED"
    assert calls == []


# -------------------------------------------------------------- provider unit
def test_provider_returns_none_when_the_auth_server_is_down() -> None:
    provider = ConsentTokenProvider()
    provider._http = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(500))
    )

    async def run() -> Any:
        try:
            return await provider.token_for(MSISDN)
        finally:
            await provider.aclose()

    token = asyncio.run(run())

    assert token is None
    assert provider.last_error  # the failure is recorded, not swallowed silently


def test_authorization_request_carries_the_spike_proven_parameters() -> None:
    captured: dict[str, Any] = {}

    def capture_handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/oauth2/v1/auth/clientcredentials":
            return httpx.Response(200, json={"client_id": "cid", "client_secret": "sec"})
        if path == "/.well-known/openid-configuration":
            return httpx.Response(
                200,
                json={
                    "authorization_endpoint": "https://auth.example/authorize",
                    "token_endpoint": "https://auth.example/token",
                },
            )
        if path == "/authorize":
            query = dict(request.url.params)
            captured.update(query)
            return httpx.Response(302, headers={"location": f"{REDIRECT}?code=c1"})
        if path == "/token":
            return httpx.Response(200, json={"access_token": "t1"})
        raise AssertionError(path)

    provider = ConsentTokenProvider()
    provider._http = httpx.AsyncClient(transport=httpx.MockTransport(capture_handler))

    async def run() -> Any:
        try:
            return await provider.token_for(MSISDN)
        finally:
            await provider.aclose()

    token = asyncio.run(run())

    assert token == "t1"
    assert captured["login_hint"] == MSISDN
    assert captured["redirect_uri"] == REDIRECT
    assert captured["response_type"] == "code"
    assert captured["scope"] == "dpv:FraudPreventionAndDetection number-verification:verify"
    assert captured["state"]


def test_token_cache_file_is_never_written_for_nv(tmp_path: Path) -> None:
    """Single-use tokens must never masquerade as recordable signal responses."""
    state: dict[str, int] = dict.fromkeys(
        ("client_credentials", "discovery", "authorize", "token_exchange", "verify"), 0
    )
    client = NacClient(mode="live", record=True, replay_dir=tmp_path)
    client._http = httpx.AsyncClient(transport=httpx.MockTransport(consent_aware_handler(state)))

    async def run() -> Any:
        async with client:
            await client.fetch(Signal.NUMBER_VERIFICATION, MSISDN)

    asyncio.run(run())

    assert list(tmp_path.glob("*.json")) == []
