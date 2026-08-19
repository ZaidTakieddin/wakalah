"""Smoke-test NacClient against the live Nokia sandbox.

Run from the backend/ directory:
    .venv\\Scripts\\python.exe -m scripts.smoke_nac

Exercises all three simulator personas (clean, compromised, error) and then
replays the recorded responses with the network path disabled, proving the
fallback returns the same normalized evidence.
"""

from __future__ import annotations

import asyncio

from app.models.domain import CORE_SPINE, ESCALATION_TOOLKIT, Signal
from app.nac.client import NacClient

CLEAN = "+99999991001"
COMPROMISED = "+99999991000"
ERROR_503 = "+99999990503"

# Number Verification needs the 3-legged consent token, so it is exercised
# separately (see backend/spike/nv_flow_probe.ps1); everything else is callable
# with application credentials alone.
TWO_LEGGED = sorted(
    (CORE_SPINE | ESCALATION_TOOLKIT) - {Signal.NUMBER_VERIFICATION},
    key=lambda s: s.value,
)


def show(title: str, bundle) -> None:
    print(f"\n=== {title} ===")
    for signal in sorted(bundle.records, key=lambda s: s.value):
        record = bundle.records[signal]
        status = "ok " if record.is_usable else "ERR"
        detail = record.result if record.is_usable else record.error_code
        print(
            f"  [{status}] {signal.value:<22} {record.dimension.value:<11}"
            f" {record.source.value:<11} {record.latency_ms or 0:>4}ms  {detail}"
        )
    print(f"  dimensions covered: {sorted(d.value for d in bundle.covered_dimensions())}")


async def main() -> None:
    calls: list[dict] = []
    async with NacClient(on_call=calls.append) as client:
        clean = await client.fetch_many(
            TWO_LEGGED,
            CLEAN,
            claimed_name="Amina Haddad",
            claimed_birthdate="1990-01-01",
        )
        show(f"CLEAN persona {CLEAN}", clean)

        compromised = await client.fetch_many(
            TWO_LEGGED,
            COMPROMISED,
            claimed_name="Amina Haddad",
            claimed_birthdate="1990-01-01",
        )
        show(f"COMPROMISED persona {COMPROMISED}", compromised)

        degraded = await client.fetch_many([Signal.SIM_SWAP, Signal.TENURE], ERROR_503)
        show(f"ERROR persona {ERROR_503} (graceful degradation)", degraded)

    async with NacClient(mode="replay") as replay_client:
        replayed = await replay_client.fetch_many(TWO_LEGGED, CLEAN)
    show(f"REPLAY of {CLEAN} (network path unused)", replayed)

    live_results = {s: r.result for s, r in clean.records.items() if r.is_usable}
    replay_results = {s: r.result for s, r in replayed.records.items() if r.is_usable}
    print(
        f"\nreplay parity: {'MATCH' if live_results == replay_results else 'MISMATCH'}"
        f"  ({len(replay_results)}/{len(live_results)} signals)"
    )
    print(f"api calls captured for the live panel: {len(calls)}")


if __name__ == "__main__":
    asyncio.run(main())
