"""End-to-end check of the HTTP API and the live WebSocket stream.

Start the server first, in another terminal:
    .venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000

Then:
    .venv\\Scripts\\python.exe -m scripts.smoke_api

Connects a WebSocket client, posts a real transaction, and prints both the
decision and every event the UI would have received while it was decided.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import websockets

BASE = "http://127.0.0.1:8000"
WS = "ws://127.0.0.1:8000/ws"


async def collect_events(seen: list[dict], ready: asyncio.Event, stop: asyncio.Event) -> None:
    async with websockets.connect(WS) as socket:
        ready.set()
        while not stop.is_set():
            try:
                raw = await asyncio.wait_for(socket.recv(), timeout=1.0)
            except TimeoutError:
                continue
            event = json.loads(raw)
            if event.get("type") != "ping":
                seen.append(event)


async def main() -> None:
    seen: list[dict] = []
    ready, stop = asyncio.Event(), asyncio.Event()
    listener = asyncio.create_task(collect_events(seen, ready, stop))
    await ready.wait()

    async with httpx.AsyncClient(timeout=180) as client:
        health = (await client.get(f"{BASE}/health")).json()
        print(f"health: {health}\n")

        payload = {
            "transactionId": "tx_api_smoke_1",
            "mandateId": "man_amina_001",
            "amount": {"value": 1800, "currency": "QAR"},
            "beneficiaryId": "ben_mother",
            "beneficiaryIsNew": True,
        }
        response = await client.post(f"{BASE}/v1/transactions/evaluate", json=payload)
        decision = response.json()

    print(f"POST /v1/transactions/evaluate -> {response.status_code}")
    print(f"  decision            : {decision['decision'].upper()}")
    print(f"  riskTier            : {decision['riskTier']}")
    print(f"  agentProposal       : {decision.get('agentProposal')}")
    print(f"  policyOverrodeAgent : {decision['policyOverrodeAgent']}")
    print(f"  reasonCodes         : {decision['reasonCodes']}")
    print(f"  challenge           : {decision.get('challenge')}")
    print(f"  latencyMs           : {decision.get('latencyMs')}")
    print("  evidenceSummary     :")
    for signal, ev in decision["evidenceSummary"].items():
        mark = "ok " if ev["available"] else "ERR"
        print(
            f"      [{mark}] {signal:<22} {ev['dimension']:<11} {ev['source']:<11} {ev['result']}"
        )

    await asyncio.sleep(0.5)
    stop.set()
    await listener

    counts: dict[str, int] = {}
    for event in seen:
        counts[event["type"]] = counts.get(event["type"], 0) + 1
    print(f"\nlive events received by the UI: {sum(counts.values())}")
    for event_type, count in sorted(counts.items()):
        print(f"  {event_type:<22} x{count}")

    print("\nagent reasoning trace as streamed:")
    for event in seen:
        if event["type"] == "agent.trace":
            step = event["payload"]
            brain = f"[{step['brain']}]" if step.get("brain") else ""
            print(f"  . {step['step']:<16} {brain:<12} {step['summary']}")


if __name__ == "__main__":
    asyncio.run(main())
