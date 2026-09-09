"""Number Verification consent â€” the operator's 3-legged OAuth flow, headless.

Number Verification is the one CAMARA signal that cannot be called with the
application's own credentials: it needs a token minted *for one subscriber*,
which is what makes its answer cryptographic rather than merely asserted
("the SIM in this device really belongs to this number").

docs/02 D23 proved the whole recipe against the sandbox, headless:

    1. GET /oauth2/v1/auth/clientcredentials   -> {client_id, client_secret}
    2. GET /.well-known/openid-configuration   -> authorize/token endpoints
    3. GET {authorize}?scope=&response_type=code&client_id=&redirect_uri=
       &login_hint={msisdn}&state=...          -> follow the redirect chain by
       hand until it lands back on our redirect_uri carrying ?code=
       (the simulator auto-approves: no browser, no login screen)
    4. POST {token} (authorization_code grant) -> access_token, SINGLE-USE
    5. POST number-verification/v0/verify with that Bearer token

Design constraints here mirror NacClient's:

    * this is the only other module allowed to talk to NaC;
    * every failure degrades to `None`, never an exception â€” mandate creation
      must survive an unreachable auth server exactly as it survives an
      unreachable signal API;
    * tokens are never cached (single-use by contract); credentials and the
      discovery document are cached for the process lifetime.
"""

from __future__ import annotations

import logging
import re
import secrets
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MAX_AUTH_HOPS = 8
"""The authorize endpoint redirects through Nokia's own login/PKCE hops before
landing on our redirect_uri. Eight was enough on the spike; more means the
chain went sideways, so stop instead of following forever."""

CODE_PATTERN = re.compile(r"[?&]code=([^&]+)")


class ConsentTokenProvider:
    """Mints single-use 3-legged Number Verification tokens."""

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None
        self._credentials: tuple[str, str] | None = None
        self._authorize: str | None = None
        self._token: str | None = None
        self.last_error: str | None = None

    async def aclose(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------ public
    async def token_for(self, msisdn: str) -> str | None:
        """One fresh token bound to `msisdn`, or None on any failure."""
        try:
            return await self._token_for(msisdn)
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"[:200]
            logger.warning("number verification consent failed - %s", self.last_error)
            return None

    # --------------------------------------------------------------- internals
    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=settings.nac_timeout_seconds)
        return self._http

    async def _token_for(self, msisdn: str) -> str | None:
        started = time.perf_counter()
        headers = dict(settings.nac_headers)

        client_id, client_secret = await self._credentials_cached(headers)
        authorize_url, token_url = await self._discovery_cached(headers)

        code = await self._authorization_code(
            authorize_url,
            client_id=client_id,
            msisdn=msisdn,
            headers=headers,
        )
        if code is None:
            return None

        token = await self._exchange_code(token_url, client_id, client_secret, code)
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info("minted NV consent token for %sâ€¦ in %dms", msisdn[-4:], latency_ms)
        return token

    async def _credentials_cached(self, headers: dict[str, str]) -> tuple[str, str]:
        if self._credentials is not None:
            return self._credentials
        response = await self._client().get(
            settings.nac_base_url + "/oauth2/v1/auth/clientcredentials", headers=headers
        )
        response.raise_for_status()
        body = response.json()
        self._credentials = (str(body["client_id"]), str(body["client_secret"]))
        return self._credentials

    async def _discovery_cached(self, headers: dict[str, str]) -> tuple[str, str]:
        if self._discovery_ready():
            assert self._authorize and self._token
            return self._authorize, self._token
        response = await self._client().get(
            settings.nac_base_url + "/.well-known/openid-configuration", headers=headers
        )
        response.raise_for_status()
        body = response.json()
        self._authorize = str(body["authorization_endpoint"])
        self._token = str(body["token_endpoint"])
        return self._authorize, self._token

    def _discovery_ready(self) -> bool:
        return self._authorize is not None and self._token is not None

    async def _authorization_code(
        self,
        authorize_url: str,
        *,
        client_id: str,
        msisdn: str,
        headers: dict[str, str],
    ) -> str | None:
        """Walk the redirect chain manually; the code arrives in a Location
        header pointed at our redirect_uri. No callback server needed."""
        params = {
            "scope": settings.nv_scope,
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": settings.nv_redirect_uri,
            "login_hint": msisdn,
            "state": secrets.token_urlsafe(8),
        }
        # Encode the query exactly once; later hops are followed verbatim so
        # our parameters are never re-appended to Nokia's own redirect URLs.
        url = str(httpx.Request("GET", authorize_url, params=params).url)
        for _hop in range(MAX_AUTH_HOPS):
            response = await self._client().get(url, headers=headers, follow_redirects=False)
            location = response.headers.get("location")
            if location is None:
                self.last_error = f"authorize chain stopped at {response.status_code}"
                logger.warning("NV consent: %s", self.last_error)
                return None
            if location.startswith(settings.nv_redirect_uri):
                match = CODE_PATTERN.search(location)
                if match is None:
                    self.last_error = "redirect landed without ?code="
                    logger.warning("NV consent: %s", self.last_error)
                    return None
                return match.group(1)
            url = (
                location if location.startswith("http") else (f"{settings.nac_base_url}{location}")
            )
        self.last_error = f"authorize chain exceeded {MAX_AUTH_HOPS} hops"
        logger.warning("NV consent: %s", self.last_error)
        return None

    async def _exchange_code(
        self, token_url: str, client_id: str, client_secret: str, code: str
    ) -> str | None:
        response = await self._client().post(
            token_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.nv_redirect_uri,
            },
        )
        response.raise_for_status()
        token: Any = response.json().get("access_token")
        return str(token) if token else None
