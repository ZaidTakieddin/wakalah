"""NacClient — the only door to Nokia Network as Code.

Architectural rule (backend/CLAUDE.md): no other module may make HTTP calls to
the network. Everything goes through here, which buys three things at once:

    1. every call is logged identically -> the audit trail and the demo's live
       API panel are fed from one place;
    2. live / replay can be swapped with a setting, so the demo survives a dead
       network without any calling code changing;
    3. provider quirks are normalized into `EvidenceRecord`, so the policy
       engine never sees raw operator JSON.

A failed signal is returned as unusable evidence, never as a pass. That
distinction is a security property, not a style choice.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.models.domain import (
    SIGNAL_DIMENSION,
    ConsentStatus,
    EvidenceBundle,
    EvidenceRecord,
    EvidenceSource,
    Signal,
)
from app.nac.consent import ConsentTokenProvider
from app.nac.endpoints import KYC_FILL_IN_PATH, SPECS

CallHook = Callable[[dict[str, Any]], None]
"""Called once per network call so the UI can render the live API panel.
Never allowed to break a verification — exceptions are swallowed."""

MAX_CONCURRENT_CALLS = 3
"""The sandbox rate-limits bursts: nine concurrent calls returned HTTP 429 on
the first live run. A plan of six signals must never fail in front of judges,
so calls are throttled and retried rather than fired all at once."""

RETRY_STATUSES = frozenset({429, 502, 503, 504})
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 0.6


def _safe_key(signal: Signal, msisdn: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.+-]", "_", f"{signal.value}__{msisdn}")


class NacClient:
    """Fetches CAMARA signals and returns normalized evidence."""

    def __init__(
        self,
        *,
        mode: str | None = None,
        record: bool | None = None,
        on_call: CallHook | None = None,
        replay_dir: Path | None = None,
        consent: ConsentTokenProvider | None = None,
    ) -> None:
        self.mode = (mode or settings.nac_mode).lower()
        self.record = settings.nac_record if record is None else record
        self.on_call = on_call
        self.replay_dir = replay_dir or settings.replay_dir
        self.replay_dir.mkdir(parents=True, exist_ok=True)
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_CALLS)
        self._http: httpx.AsyncClient | None = None
        self.consent = consent or ConsentTokenProvider()
        self._ttl_cache: dict[tuple[str, str], tuple[float, EvidenceRecord]] = {}
        """(signal, msisdn, params-hash) -> (expiry, record). Only usable LIVE
        evidence is cached; a reused answer is relabelled `cached`, never `live`
        — the honesty label travels with the data."""

    @property
    def _cache_ttl(self) -> float:
        return settings.nac_cache_ttl_seconds

    async def aclose(self) -> None:
        """Close the shared connection pool."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        await self.consent.aclose()

    async def __aenter__(self) -> NacClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    def _http_client(self) -> httpx.AsyncClient:
        # One pooled client per NacClient: reusing connections is both faster and
        # gentler on the sandbox's rate limiter than a new client per call.
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=settings.nac_timeout_seconds)
        return self._http

    # ------------------------------------------------------------------ public
    async def fetch(
        self,
        signal: Signal,
        msisdn: str,
        *,
        access_token: str | None = None,
        **params: Any,
    ) -> EvidenceRecord:
        """Fetch one signal. Always returns a record — failures are evidence too."""
        spec = SPECS[signal]
        body = spec.build_body(msisdn, params)

        if self.mode == "live":
            cached = self._cache_get(signal, msisdn, body)
            if cached is not None:
                return cached

        token = access_token
        if spec.needs_bearer:
            if not token and self.mode == "live":
                # Mint the 3-legged consent token on the fly (docs/02 D23 recipe).
                token = await self.consent.token_for(msisdn)
            if not token:
                message = (
                    "Number Verification needs a 3-legged consent token; the "
                    "consent flow is unavailable right now."
                    if self.mode == "live"
                    else "Number Verification needs a 3-legged consent token; "
                    "run the operator consent flow first."
                )
                return self._unavailable(
                    signal,
                    msisdn,
                    code="CONSENT_TOKEN_REQUIRED",
                    message=message,
                )

        if self.mode == "replay":
            return self._from_replay(signal, msisdn, body)

        headers = dict(settings.nac_headers)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = settings.nac_base_url + spec.path

        started = time.perf_counter()
        response: httpx.Response | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                async with self._semaphore:
                    response = await self._http_client().post(url, headers=headers, json=body)
            except httpx.HTTPError as exc:
                self._emit(signal, msisdn, spec.path, body, None, exc.__class__.__name__, 0)
                return self._unavailable(signal, msisdn, code="NETWORK_ERROR", message=str(exc))

            # Transient upstream conditions (rate limiting, gateway hiccups) get a
            # backoff and another try; anything else is a real answer.
            if response.status_code not in RETRY_STATUSES or attempt == MAX_ATTEMPTS:
                break
            await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))

        assert response is not None
        latency_ms = int((time.perf_counter() - started) * 1000)
        raw = self._parse(response)
        self._emit(signal, msisdn, spec.path, body, response.status_code, raw, latency_ms)

        if response.status_code >= 400:
            # The 04xx/05xx simulator personas land here on purpose: this is the
            # graceful-degradation path we demo, not an accident.
            code, message = self._camara_error(raw, response.status_code)
            return self._unavailable(
                signal, msisdn, code=code, message=message, latency_ms=latency_ms
            )

        if self.record:
            self._write_replay(signal, msisdn, raw)

        record = EvidenceRecord(
            signal=signal,
            dimension=SIGNAL_DIMENSION[signal],
            subject={"phoneNumber": msisdn},
            result=spec.normalize(raw),
            source=EvidenceSource.LIVE,
            latency_ms=latency_ms,
            consent_status=(
                ConsentStatus.GRANTED
                if spec.needs_bearer
                else ConsentStatus.NOT_REQUIRED_AT_RUNTIME
            ),
        )
        self._cache_put(signal, msisdn, body, record)
        return record

    async def fetch_identity(self, msisdn: str) -> dict[str, Any] | None:
        """Operator-held registration data for a number (CAMARA KYC Fill-in).

        Used at mandate creation to autofill a principal's identity from the
        operator instead of asking them to type it — the "instant onboarding"
        case for people without deep document history. Returns None when the
        operator or market does not support it; onboarding then falls back to
        the identity the partner asserts.
        """
        if self.mode == "replay":
            return None
        try:
            response = await self._http_client().post(
                settings.nac_base_url + KYC_FILL_IN_PATH,
                headers=settings.nac_headers,
                json={"phoneNumber": msisdn},
            )
        except httpx.HTTPError:
            return None

        raw = self._parse(response)
        self._emit(
            Signal.KYC_MATCH,
            msisdn,
            KYC_FILL_IN_PATH,
            {"phoneNumber": msisdn},
            response.status_code,
            {"identity_autofilled": response.status_code < 400},
            0,
        )
        if response.status_code >= 400 or not isinstance(raw, dict):
            return None
        return raw

    async def fetch_many(
        self,
        signals: Iterable[Signal],
        msisdn: str,
        *,
        access_token: str | None = None,
        **params: Any,
    ) -> EvidenceBundle:
        """Fetch several signals concurrently.

        Concurrency is a product requirement, not an optimisation: a checkout has
        a latency budget, and running a six-signal plan sequentially would spend
        it on waiting.
        """
        signal_list = list(signals)
        results = await asyncio.gather(
            *(self.fetch(s, msisdn, access_token=access_token, **params) for s in signal_list),
            return_exceptions=True,
        )

        bundle = EvidenceBundle()
        for signal, result in zip(signal_list, results, strict=True):
            if isinstance(result, BaseException):
                bundle.add(
                    self._unavailable(signal, msisdn, code="CLIENT_ERROR", message=str(result))
                )
            else:
                bundle.add(result)
        return bundle

    # ----------------------------------------------------------------- internals
    @staticmethod
    def _cache_key(signal: Signal, msisdn: str, body: dict[str, Any]) -> tuple[str, str]:
        # The request body is part of the key: "swapped in 24h" and
        # "swapped in 720h" are different questions, not different labels.
        return (signal.value, f"{msisdn}|{json.dumps(body, sort_keys=True)}")

    def _cache_get(
        self, signal: Signal, msisdn: str, body: dict[str, Any]
    ) -> EvidenceRecord | None:
        if self._cache_ttl <= 0:
            return None
        entry = self._ttl_cache.get(self._cache_key(signal, msisdn, body))
        if entry is None:
            return None
        expires_at, record = entry
        if time.monotonic() >= expires_at:
            del self._ttl_cache[self._cache_key(signal, msisdn, body)]
            return None
        return record.model_copy(update={"source": EvidenceSource.CACHED})

    def _cache_put(
        self, signal: Signal, msisdn: str, body: dict[str, Any], record: EvidenceRecord
    ) -> None:
        if self._cache_ttl <= 0 or not record.is_usable:
            # A failed call is never cached: an outage must not look like data.
            return
        key = self._cache_key(signal, msisdn, body)
        self._ttl_cache[key] = (time.monotonic() + self._cache_ttl, record)

    @staticmethod
    def _parse(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return {"_raw_text": response.text[:500]}

    @staticmethod
    def _camara_error(raw: Any, status_code: int) -> tuple[str, str]:
        if isinstance(raw, dict):
            return (
                str(raw.get("code") or f"HTTP_{status_code}"),
                str(raw.get("message") or ""),
            )
        return f"HTTP_{status_code}", ""

    def _unavailable(
        self,
        signal: Signal,
        msisdn: str,
        *,
        code: str,
        message: str,
        latency_ms: int | None = None,
    ) -> EvidenceRecord:
        return EvidenceRecord(
            signal=signal,
            dimension=SIGNAL_DIMENSION[signal],
            subject={"phoneNumber": msisdn},
            result={},
            source=EvidenceSource.UNAVAILABLE,
            ok=False,
            error_code=code,
            error_message=message,
            latency_ms=latency_ms,
            consent_status=ConsentStatus.UNKNOWN,
        )

    def _replay_path(self, signal: Signal, msisdn: str) -> Path:
        return self.replay_dir / f"{_safe_key(signal, msisdn)}.json"

    def _write_replay(self, signal: Signal, msisdn: str, raw: Any) -> None:
        # Recording is best-effort; never fail a verification over it.
        with contextlib.suppress(OSError):
            self._replay_path(signal, msisdn).write_text(
                json.dumps(raw, indent=2), encoding="utf-8"
            )

    def _from_replay(self, signal: Signal, msisdn: str, body: dict[str, Any]) -> EvidenceRecord:
        path = self._replay_path(signal, msisdn)
        if not path.exists():
            return self._unavailable(
                signal,
                msisdn,
                code="NO_REPLAY_DATA",
                message=f"No recorded response for {signal.value} / {msisdn}",
            )
        raw = json.loads(path.read_text(encoding="utf-8"))
        self._emit(signal, msisdn, SPECS[signal].path, body, 200, raw, 0, replay=True)
        return EvidenceRecord(
            signal=signal,
            dimension=SIGNAL_DIMENSION[signal],
            subject={"phoneNumber": msisdn},
            result=SPECS[signal].normalize(raw),
            source=EvidenceSource.REPLAY,
            latency_ms=0,
        )

    def _emit(
        self,
        signal: Signal,
        msisdn: str,
        path: str,
        request: dict[str, Any],
        status: int | None,
        response: Any,
        latency_ms: int,
        *,
        replay: bool = False,
    ) -> None:
        if self.on_call is None:
            return
        # The UI panel must never be able to break a decision.
        with contextlib.suppress(Exception):
            self.on_call(
                {
                    "type": "nac.call",
                    "signal": signal.value,
                    "path": path,
                    "request": request,
                    "status": status,
                    "response": response,
                    "latency_ms": latency_ms,
                    "source": "replay" if replay else "live",
                    "simulated_device": msisdn.startswith("+9999999"),
                }
            )
