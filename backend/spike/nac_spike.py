"""NaC API spike — Week 1 (docs/02-week1-gate.md §2).

Runs each candidate CAMARA API against Nokia Network-as-Code simulators via
RapidAPI and writes raw results to spike-results.json, printing a summary
table to fill the doc-02 matrix. Endpoint paths were harvested from the
NaC MCP tool schemas on 2026-07-06 — if one 404s, check the current path
on the RapidAPI/NaC portal and adjust ENDPOINTS below.

Read-only calls by default. Set SPIKE_MUTATIONS=1 to also test
QoD session create/delete and geofencing subscription create/delete
(both are cleaned up in the same run).

Setup:
    cd backend/spike
    copy .env.example .env      (then fill RAPIDAPI_KEY — never commit .env)
    pip install requests
    python nac_spike.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------- env
def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

load_env(Path(__file__).parent / ".env")

KEY = os.environ.get("RAPIDAPI_KEY", "")
BASE = os.environ.get("NAC_BASE_URL", "https://network-as-code.p-eu.rapidapi.com")
HOST = os.environ.get("NAC_RAPIDAPI_HOST", "network-as-code.nokia.rapidapi.com")
PHONE = os.environ.get("DEVICE_PHONE", "+99999991000")  # roster personas: see .env.example
NAI = os.environ.get("DEVICE_NAI", "8D8AC610-566D-4EF0-9C22-186B2A5ED793-1000@testcsp.net")
SINK = os.environ.get("SINK_URL", "https://example.com/nac-sink")  # tunnel URL later
MUTATIONS = os.environ.get("SPIKE_MUTATIONS", "0") == "1"

if not KEY:
    sys.exit("RAPIDAPI_KEY missing — copy .env.example to .env and fill it in.")

HEADERS = {
    "X-RapidAPI-Key": KEY,
    "X-RapidAPI-Host": HOST,
    "Content-Type": "application/json",
}

DEVICE = {"phoneNumber": PHONE}
AREA = {  # Dubai downtown, 2 km — arbitrary demo zone
    "areaType": "CIRCLE",
    "center": {"latitude": 25.276987, "longitude": 55.296249},
    "radius": 2000,
}

# name -> (path, body)  — paths from MCP schemas, 2026-07-06
ENDPOINTS: dict[str, tuple[str, dict]] = {
    "sim_swap_check": (
        "/passthrough/camara/v1/sim-swap/sim-swap/v0/check",
        {"phoneNumber": PHONE, "maxAge": 240},
    ),
    "sim_swap_retrieve_date": (
        "/passthrough/camara/v1/sim-swap/sim-swap/v0/retrieve-date",
        {"phoneNumber": PHONE},
    ),
    "device_swap_check": (
        "/passthrough/camara/v1/device-swap/device-swap/v1/check",
        {"phoneNumber": PHONE, "maxAge": 240},
    ),
    "reachability": (
        "/device-status/device-reachability-status/v1/retrieve",
        {"device": DEVICE},
    ),
    "roaming": (
        "/device-status/device-roaming-status/v1/retrieve",
        {"device": DEVICE},
    ),
    "location_retrieve": (
        "/location-retrieval/v0/retrieve",
        {"device": DEVICE, "maxAge": 3600},
    ),
    "location_verify": (
        "/location-verification/v1/verify",
        {"device": DEVICE, "area": AREA},
    ),
    "congestion_query": (
        "/congestion-insights/v0/query",
        {"device": DEVICE},  # no window -> predicts next 15 min
    ),
    "connectivity": (
        "/device-status/v0/connectivity",
        {"device": DEVICE},
    ),
    # --- identity goldmine (docs/08 §1) — sandbox behavior of these decides
    # --- the Wakalah-vs-MIZAN gate (docs/02 §5)
    "tenure_check": (
        "/passthrough/camara/v1/kyc-tenure/kyc-tenure/v0.1/check-tenure",
        {"phoneNumber": PHONE, "tenureDate": "2023-01-01"},
    ),
    "number_recycling_check": (
        "/passthrough/camara/v1/number-recycling/number-recycling/v0.2/check",
        {"phoneNumber": PHONE, "specifiedDate": "2025-01-01"},
    ),
    "call_forwarding_unconditional": (
        "/passthrough/camara/v1/call-forwarding-signal/call-forwarding-signal/v0.3/unconditional-call-forwardings",
        {"phoneNumber": PHONE},
    ),
    "kyc_match_minimal": (
        "/passthrough/camara/v1/kyc-match/kyc-match/v0.3/match",
        {"phoneNumber": PHONE, "name": "Test User", "birthdate": "1990-01-01"},
    ),
    "age_verification": (
        "/passthrough/camara/v1/kyc-age-verification/kyc-age-verification/v0.1/verify",
        {"phoneNumber": PHONE, "ageThreshold": 18},
    ),
    # Number Verification is expected to FAIL here: it needs the three-legged
    # CSP auth flow (authorization code). The failure mode itself is the
    # spike datum — record it.
    "number_verification_no_code": (
        "/passthrough/camara/v1/number-verification/number-verification/v0/verify",
        {"phoneNumber": PHONE},
    ),
}


def call(name: str, path: str, body: dict, method: str = "POST") -> dict:
    try:
        r = requests.request(method, BASE + path, headers=HEADERS, json=body, timeout=30)
        try:
            payload = r.json()
        except ValueError:
            payload = r.text[:2000]
        result = {"status": r.status_code, "body": payload}
    except requests.RequestException as e:
        result = {"status": "EXCEPTION", "body": str(e)}
    print(f"{name:32s} -> {result['status']}")
    return result


def main() -> None:
    results: dict[str, dict] = {"_meta": {
        "ts": datetime.now(timezone.utc).isoformat(),
        "base": BASE, "phone": PHONE, "mutations": MUTATIONS,
    }}

    for name, (path, body) in ENDPOINTS.items():
        results[name] = call(name, path, body)

    if MUTATIONS:
        # --- QoD session: create -> delete -------------------------------
        qod_body = {
            "qosProfile": "QOS_E",
            # QoD is flow-oriented: device MUST carry an ipv4Address (confirmed Jul 7 — 400 without, 201 with)
            "device": {**DEVICE, "ipv4Address": {"publicAddress": "1.1.1.2", "privateAddress": "1.1.1.2"}},
            "applicationServer": {"ipv4Address": "5.6.7.8"},
            "duration": 60,
        }
        created = call("qod_create", "/qod/v0/sessions", qod_body)
        results["qod_create"] = created
        sid = created.get("body", {}).get("sessionId") if isinstance(created.get("body"), dict) else None
        if sid:
            results["qod_delete"] = call("qod_delete", f"/qod/v0/sessions/{sid}", {}, "DELETE")

        # --- Geofencing subscription: create -> delete --------------------
        geo_body = {
            "protocol": "HTTP",
            "sink": SINK,
            "types": ["org.camaraproject.geofencing-subscriptions.v0.area-entered"],
            "config": {
                "subscriptionDetail": {"device": DEVICE, "area": AREA},
                "initialEvent": True,   # fires immediately if already inside — demo gold
                "subscriptionMaxEvents": 5,
                "subscriptionExpireTime": (
                    datetime.now(timezone.utc) + timedelta(hours=1)
                ).isoformat().replace("+00:00", "Z"),
            },
        }
        created = call("geofence_create", "/geofencing-subscriptions/v0.3/subscriptions", geo_body)
        results["geofence_create"] = created
        gid = created.get("body", {}).get("id") if isinstance(created.get("body"), dict) else None
        if gid:
            results["geofence_delete"] = call(
                "geofence_delete", f"/geofencing-subscriptions/v0.3/subscriptions/{gid}", {}, "DELETE"
            )

    out = Path(__file__).parent / "spike-results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nRaw results -> {out}")
    print("Fill the matrix in docs/02-week1-gate.md §2 from these statuses/bodies.")


if __name__ == "__main__":
    main()
