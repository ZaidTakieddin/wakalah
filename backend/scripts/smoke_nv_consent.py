"""Live smoke test: Number Verification's 3-legged consent flow at runtime.

Run from the backend/ directory:
    .venv\\Scripts\\python.exe -m scripts.smoke_nv_consent

Proves the D23 recipe works through app/nac/consent.py + NacClient against the
real sandbox — the exact path a mandate creation would take, not the spike
script. Prints verdicts, latencies and error codes only; tokens and secrets
are never printed.
"""

from __future__ import annotations

import asyncio
import sys
import time

from app.config import settings
from app.models.domain import Signal
from app.nac.client import NacClient

PERSONAS = {
    "clean": "+99999991001",
    "compromised": "+99999991000",
}


async def main() -> int:
    if settings.nac_mode != "live":
        print(f"NAC_MODE={settings.nac_mode} — this smoke needs live mode")
        return 2
    if not settings.rapidapi_key:
        print("RAPIDAPI_KEY missing from backend/.env")
        return 2

    calls = 0

    def on_call(payload: dict) -> None:
        nonlocal calls
        calls += 1
        status = payload.get("status")
        latency = payload.get("latency_ms", 0)
        print(f"  [nac.call] {payload['signal']} status={status} {latency}ms")

    failures = 0
    started = time.perf_counter()
    async with NacClient(mode="live", record=False, on_call=on_call) as client:
        for label, msisdn in PERSONAS.items():
            record = await client.fetch(Signal.NUMBER_VERIFICATION, msisdn)
            if record.is_usable:
                detail = f"verified={record.result.get('number_verified')}"
                consent = record.consent_status.value
            else:
                detail = record.error_message or record.error_code
                consent = record.consent_status.value
                failures += 1
            state = "ok " if record.is_usable else "ERR"
            latency = record.latency_ms or 0
            print(
                f"[{state}] {label:<12} {msisdn}  "
                f"{record.source.value:<5} consent={consent:<22} {latency:>5}ms  {detail}"
            )

    seconds = time.perf_counter() - started
    print(f"\n{calls} network call(s) emitted · total {seconds:.1f}s")
    print("RESULT:", "PASS" if failures == 0 else f"FAIL ({failures} unusable)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
