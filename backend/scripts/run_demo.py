"""Run the whole demo story against a running server — the rehearsal command.

    .venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000
    .venv\\Scripts\\python.exe -m scripts.run_demo

Prints each beat with what it expected and what actually happened, so a
rehearsal either passes visibly or fails visibly.
"""

from __future__ import annotations

import asyncio

import httpx

BASE = "http://127.0.0.1:8000"


async def main() -> None:
    async with httpx.AsyncClient(timeout=900) as client:
        script = (await client.get(f"{BASE}/v1/scenario")).json()
        expectations = {b["id"]: b["expect"] for b in script["beats"]}

        response = await client.post(f"{BASE}/v1/scenario/run-all")
        results = response.json()["results"]

    for result in results:
        mark = "OK " if result["ok"] else "ERR"
        print(f"\n[{mark}] {result['beat_id']}  —  {result['title']}")
        print(f"      expected : {expectations.get(result['beat_id'], '')}")
        print(f"      actual   : {result['summary']}")
        detail = result["detail"]
        if "reasonCodes" in detail:
            print(
                f"      agent={detail['agentProposal']}  "
                f"policyOverrode={detail['policyOverrodeAgent']}  "
                f"reasons={detail['reasonCodes']}"
            )
            print(f"      signals  : {', '.join(detail['signals'])}")

    print(f"\n{sum(1 for r in results if r['ok'])}/{len(results)} beats ran")


if __name__ == "__main__":
    asyncio.run(main())
