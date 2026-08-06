"""Prove the audit trail: run a transaction, then read it back from storage.

Server must be running:
    .venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000

Then:
    .venv\\Scripts\\python.exe -m scripts.smoke_audit
"""

from __future__ import annotations

import asyncio

import httpx

BASE = "http://127.0.0.1:8000"
MSISDN = "+99999991001"


async def main() -> None:
    async with httpx.AsyncClient(timeout=300) as client:
        health = (await client.get(f"{BASE}/health")).json()
        print(f"audit backend: {health['audit_backend']}")

        mandate = (
            await client.post(
                f"{BASE}/v1/mandates",
                json={
                    "principalMsisdn": MSISDN,
                    "agentId": "agent_rasheed",
                    "agentKeyFingerprint": "fp_ed25519_demo",
                    "amountLimit": 2000,
                    "beneficiaryIds": ["ben_mother"],
                },
            )
        ).json()
        print(
            f"mandate {mandate['mandateId']} for '{mandate['principalId']}' "
            "(identity autofilled from the operator)"
        )

        response = await client.post(
            f"{BASE}/v1/transactions/evaluate",
            json={
                "transactionId": "tx_audit_demo",
                "mandateId": mandate["mandateId"],
                "amount": {"value": 1500, "currency": "QAR"},
                "beneficiaryId": "ben_mother",
                "beneficiaryIsNew": True,
            },
        )
        decision = response.json()
        print(
            f"\ndecision  : {decision['decision'].upper()}  tier={decision['riskTier']}"
            f"  agent={decision.get('agentProposal')}"
            f"  overrode={decision['policyOverrodeAgent']}"
        )
        print(f"reasons   : {decision['reasonCodes']}")
        print(f"signals   : {len(decision['evidenceSummary'])}")

        history = (await client.get(f"{BASE}/v1/principals/{MSISDN}/history")).json()
        print(f"\nprincipalRef (hashed) : {history['principalRef']}")
        print(f"backend               : {history['backend']}")
        print(f"decisions on record   : {len(history['decisions'])}")
        for row in history["decisions"][:5]:
            print(
                f"  {row['decided_at'][:19]}  {row['verdict']:<8} {row['risk_tier']:<7}"
                f" agent={row['agent_proposal']}  {row['reason_codes']}"
            )


if __name__ == "__main__":
    asyncio.run(main())
