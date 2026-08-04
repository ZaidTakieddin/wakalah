"""CAMARA endpoint map for Nokia Network as Code.

Every piece of "how does this API work" knowledge lives here: the paths, the
request bodies, and the translation from each provider's reply into our
normalized `result` dict. Nothing else in the codebase needs to know that
SIM Swap lives under /passthrough/camara/v1/... .

Paths were verified live against the sandbox (see backend/spike/ and
docs/08-nac-api-catalog.md). If Nokia moves an endpoint, this file is the only
thing that changes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.models.domain import Signal

# Default demo area: Budapest, where the Nokia simulators "live" (docs/08).
DEFAULT_AREA: dict[str, Any] = {
    "areaType": "CIRCLE",
    "center": {"latitude": 47.44178899529922, "longitude": 19.160422047462603},
    "radius": 50_000,
}


@dataclass(frozen=True)
class SignalSpec:
    """How to call one CAMARA signal and how to read its answer."""

    signal: Signal
    path: str
    build_body: Callable[[str, dict[str, Any]], dict[str, Any]]
    normalize: Callable[[dict[str, Any]], dict[str, Any]]
    needs_bearer: bool = False
    """Number Verification requires a 3-legged consent token; the rest are
    callable with the application credentials alone."""


# --------------------------------------------------------------- body builders
def _phone_body(msisdn: str, params: dict[str, Any]) -> dict[str, Any]:
    return {"phoneNumber": msisdn}


def _phone_with_max_age(msisdn: str, params: dict[str, Any]) -> dict[str, Any]:
    # The agent tightens max_age for higher-risk transactions: "was there a swap
    # in the last 24 hours?" is a stricter question than "in the last 10 days".
    return {"phoneNumber": msisdn, "maxAge": int(params.get("max_age_hours", 240))}


def _device_body(msisdn: str, params: dict[str, Any]) -> dict[str, Any]:
    return {"device": {"phoneNumber": msisdn}}


def _recycling_body(msisdn: str, params: dict[str, Any]) -> dict[str, Any]:
    since = params.get("since_date") or (date.today() - timedelta(days=365)).isoformat()
    return {"phoneNumber": msisdn, "specifiedDate": since}


def _tenure_body(msisdn: str, params: dict[str, Any]) -> dict[str, Any]:
    since = params.get("tenure_date") or (date.today() - timedelta(days=365)).isoformat()
    return {"phoneNumber": msisdn, "tenureDate": since}


def _kyc_body(msisdn: str, params: dict[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {"phoneNumber": msisdn}
    if name := params.get("claimed_name"):
        body["name"] = name
    if birthdate := params.get("claimed_birthdate"):
        body["birthdate"] = birthdate
    if id_document := params.get("claimed_id_document"):
        body["idDocument"] = id_document
    return body


def _location_body(msisdn: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "device": {"phoneNumber": msisdn},
        "area": params.get("area", DEFAULT_AREA),
        "maxAge": int(params.get("location_max_age_seconds", 3600)),
    }


# ----------------------------------------------------------------- normalizers
def _norm_swap(raw: dict[str, Any]) -> dict[str, Any]:
    return {"swapped": bool(raw.get("swapped"))}


def _norm_call_forwarding(raw: dict[str, Any]) -> dict[str, Any]:
    return {"forwarding_active": bool(raw.get("active"))}


def _norm_recycling(raw: dict[str, Any]) -> dict[str, Any]:
    return {"recycled": bool(raw.get("phoneNumberRecycled"))}


def _norm_tenure(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "tenure_confirmed": bool(raw.get("tenureDateCheck")),
        "contract_type": raw.get("contractType"),
    }


def _norm_kyc(raw: dict[str, Any]) -> dict[str, Any]:
    # CAMARA returns per-attribute "true"/"false"/"not_available" strings, and
    # only for the attributes that were asked about.
    matches = {k: v for k, v in raw.items() if k.endswith("Match")}
    verdicts = [str(v).lower() for v in matches.values()]
    return {
        "attributes": matches,
        "all_matched": bool(verdicts) and all(v == "true" for v in verdicts),
        "any_mismatch": any(v == "false" for v in verdicts),
    }


def _norm_reachability(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "reachable": bool(raw.get("reachable")),
        "connectivity": raw.get("connectivity", []),
        "last_status_time": raw.get("lastStatusTime"),
    }


def _norm_roaming(raw: dict[str, Any]) -> dict[str, Any]:
    country = raw.get("countryName")
    if isinstance(country, list):
        country = country[0] if country else None
    return {
        "roaming": bool(raw.get("roaming")),
        "country_code": raw.get("countryCode"),
        "country": country,
    }


def _norm_location(raw: dict[str, Any]) -> dict[str, Any]:
    result = str(raw.get("verificationResult", "UNKNOWN")).upper()
    return {
        "verification_result": result,
        "in_expected_area": result == "TRUE",
        "last_location_time": raw.get("lastLocationTime"),
    }


def _norm_number_verification(raw: dict[str, Any]) -> dict[str, Any]:
    return {"number_verified": bool(raw.get("devicePhoneNumberVerified"))}


# ------------------------------------------------------------------- the map
SPECS: dict[Signal, SignalSpec] = {
    Signal.SIM_SWAP: SignalSpec(
        signal=Signal.SIM_SWAP,
        path="/passthrough/camara/v1/sim-swap/sim-swap/v0/check",
        build_body=_phone_with_max_age,
        normalize=_norm_swap,
    ),
    Signal.DEVICE_SWAP: SignalSpec(
        signal=Signal.DEVICE_SWAP,
        path="/passthrough/camara/v1/device-swap/device-swap/v1/check",
        build_body=_phone_with_max_age,
        normalize=_norm_swap,
    ),
    Signal.CALL_FORWARDING: SignalSpec(
        signal=Signal.CALL_FORWARDING,
        path=(
            "/passthrough/camara/v1/call-forwarding-signal/"
            "call-forwarding-signal/v0.3/unconditional-call-forwardings"
        ),
        build_body=_phone_body,
        normalize=_norm_call_forwarding,
    ),
    Signal.NUMBER_RECYCLING: SignalSpec(
        signal=Signal.NUMBER_RECYCLING,
        path="/passthrough/camara/v1/number-recycling/number-recycling/v0.2/check",
        build_body=_recycling_body,
        normalize=_norm_recycling,
    ),
    Signal.TENURE: SignalSpec(
        signal=Signal.TENURE,
        path="/passthrough/camara/v1/kyc-tenure/kyc-tenure/v0.1/check-tenure",
        build_body=_tenure_body,
        normalize=_norm_tenure,
    ),
    Signal.KYC_MATCH: SignalSpec(
        signal=Signal.KYC_MATCH,
        path="/passthrough/camara/v1/kyc-match/kyc-match/v0.3/match",
        build_body=_kyc_body,
        normalize=_norm_kyc,
    ),
    Signal.REACHABILITY: SignalSpec(
        signal=Signal.REACHABILITY,
        path="/device-status/device-reachability-status/v1/retrieve",
        build_body=_device_body,
        normalize=_norm_reachability,
    ),
    Signal.ROAMING: SignalSpec(
        signal=Signal.ROAMING,
        path="/device-status/device-roaming-status/v1/retrieve",
        build_body=_device_body,
        normalize=_norm_roaming,
    ),
    Signal.LOCATION_VERIFICATION: SignalSpec(
        signal=Signal.LOCATION_VERIFICATION,
        path="/location-verification/v1/verify",
        build_body=_location_body,
        normalize=_norm_location,
    ),
    Signal.NUMBER_VERIFICATION: SignalSpec(
        signal=Signal.NUMBER_VERIFICATION,
        path=(
            "/passthrough/camara/v1/number-verification/"
            "number-verification/v0/verify"
        ),
        build_body=_phone_body,
        normalize=_norm_number_verification,
        needs_bearer=True,
    ),
}
