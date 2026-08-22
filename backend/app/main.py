"""The Wakalah service.

    POST /v1/mandates                  create a mandate (the wakalah contract)
    POST /v1/transactions/evaluate     the main endpoint: allow / challenge / deny
    GET  /v1/transactions/{id}         decision + audit reference lookup
    GET  /v1/mandates                  list mandates (demo convenience)
    WS   /ws                           live event stream for the demo UI
    GET  /health                       readiness, including which brains answer

This is where the layers meet: the API takes a partner request, the supervisor
reasons over it, NacClient fetches evidence, and the policy engine decides. The
event bus carries every network call and every reasoning step out to the UI as
it happens.

Run it:  .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.agents.brains import BrainRouter
from app.agents.schemas import TraceStep
from app.agents.supervisor import WakalahSupervisor
from app.api.schemas import (
    CreateMandateRequest,
    EvaluateRequest,
    EvaluateResponse,
    MandateResponse,
)
from app.config import settings
from app.events import bus
from app.models.domain import (
    Mandate,
    MandateScope,
    MandateStatus,
    TransactionRequest,
    utc_now,
)
from app.nac.client import NacClient
from app.policy.engine import PolicyEngine
from app.scenario.engine import BeatResult, BeatRunner, ScenarioEngine, scenario
from app.scenario.script import COMPROMISED_MSISDN, UNAVAILABLE_MSISDN, Beat
from app.store import memory
from app.store.audit import audit, principal_ref

DEMO_MANDATE_ID = "man_amina_001"
NO_MANDATE_YET = "No mandate yet — run the 'mandate' beat first"

_nac: NacClient | None = None
_policy = PolicyEngine()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """One pooled NacClient for the process; seed the demo mandate."""
    global _nac
    _nac = NacClient(on_call=lambda payload: bus.publish("nac.call", payload))
    _seed_demo_mandate()
    yield
    await _nac.aclose()
    _nac = None


app = FastAPI(
    title="Wakalah",
    version="0.1.0",
    summary="Trust layer for AI-agent transactions, on Nokia Network-as-Code CAMARA APIs",
    lifespan=lifespan,
)

# The demo UI is served from a different origin (Vite/Next dev server).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _seed_demo_mandate() -> None:
    """Amina's standing mandate, so the API is usable the moment it starts."""
    if memory.mandates.get(DEMO_MANDATE_ID) is not None:
        return
    memory.mandates.put(
        Mandate(
            mandate_id=DEMO_MANDATE_ID,
            principal_id="Amina Haddad",
            principal_msisdn="+99999991001",
            agent_id="agent_rasheed",
            agent_key_fingerprint="fp_rasheed_ed25519",
            scope=MandateScope(amount_limit=2000, beneficiary_ids=["ben_mother"]),
        )
    )


def _nac_client() -> NacClient:
    if _nac is None:  # pragma: no cover - only outside the app lifespan
        raise HTTPException(status_code=503, detail="service starting")
    return _nac


# --------------------------------------------------------------------- health
@app.get("/health")
async def health() -> dict[str, Any]:
    router = BrainRouter()
    return {
        "status": "ok",
        "nac_mode": settings.nac_mode,
        "policy_version": _policy.version,
        "brains_configured": router.configured(),
        "audit_backend": audit.backend,
        "mandates": len(memory.mandates.list_all()),
        "decisions": len(memory.decisions.list_all()),
        "ws_subscribers": bus.subscriber_count,
    }


@app.get("/v1/principals/{msisdn}/history")
async def principal_history(msisdn: str, limit: int = 20) -> dict[str, Any]:
    """The compliance-officer view: recent decisions for one principal.

    Served from the audit trail, keyed by the pseudonymous principal reference
    rather than the phone number.
    """
    return {
        "principalRef": principal_ref(msisdn),
        "backend": audit.backend,
        "decisions": await audit.history_for(msisdn, limit=limit),
    }


# -------------------------------------------------------------------- mandates
@app.post("/v1/mandates", response_model=MandateResponse, status_code=201)
async def create_mandate(request: CreateMandateRequest) -> MandateResponse:
    """Create a mandate.

    In production the principal completes the operator consent flow (Number
    Verification) before this returns; on the sandbox that flow auto-approves,
    which we state rather than imply (docs/04 section 3).
    """
    # Instant onboarding: ask the operator for the identity registered against
    # this number instead of making the principal type it (CAMARA KYC Fill-in).
    # This is the case that matters for people without deep document history.
    registered = await _nac_client().fetch_identity(request.principal_msisdn)
    principal_name = request.principal_name or (registered or {}).get("name", "")

    mandate = Mandate(
        mandate_id=memory.next_id("man"),
        principal_id=principal_name,
        principal_msisdn=request.principal_msisdn,
        agent_id=request.agent_id,
        agent_key_fingerprint=request.agent_key_fingerprint,
        scope=MandateScope(
            amount_limit=request.amount_limit,
            currency=request.currency,
            beneficiary_ids=request.beneficiary_ids,
        ),
    )
    memory.mandates.put(mandate)
    await audit.record_mandate(mandate)
    bus.publish(
        "mandate.updated",
        {
            "mandateId": mandate.mandate_id,
            "status": mandate.status.value,
            "identityAutofilledByOperator": registered is not None,
        },
    )
    return _mandate_response(mandate)


@app.get("/v1/mandates", response_model=list[MandateResponse])
async def list_mandates() -> list[MandateResponse]:
    return [_mandate_response(m) for m in memory.mandates.list_all()]


@app.post("/v1/mandates/{mandate_id}/revoke", response_model=MandateResponse)
async def revoke_mandate(mandate_id: str, reason: str = "sim_swap_detected") -> MandateResponse:
    """Revoke a mandate and put the principal into challenge-only mode.

    This is the endpoint the Sentinel will call when the operator pushes a
    SIM-swap event. Exposed now so the demo can trigger the moment on cue.
    """
    mandate = memory.mandates.set_status(mandate_id, MandateStatus.REVOKED, reason)
    if mandate is None:
        raise HTTPException(status_code=404, detail="mandate not found")
    bus.publish(
        "mandate.revoked",
        {"mandateId": mandate_id, "reason": reason, "status": mandate.status.value},
    )
    return _mandate_response(mandate)


# ---------------------------------------------------------------- transactions
@app.post("/v1/transactions/evaluate", response_model=EvaluateResponse)
async def evaluate_transaction(request: EvaluateRequest) -> EvaluateResponse:
    """The main endpoint: should this agent-initiated transaction proceed?"""
    mandate = memory.mandates.get(request.mandate_id)
    if mandate is None:
        raise HTTPException(status_code=404, detail="mandate not found")

    tx = TransactionRequest(
        transaction_id=request.transaction_id,
        mandate_id=request.mandate_id,
        partner_id=request.partner_id,
        action=request.action,
        amount=request.amount.value,
        currency=request.amount.currency,
        beneficiary_id=request.beneficiary_id,
        beneficiary_is_new=request.beneficiary_is_new,
        channel=request.channel,
    )

    def on_trace(step: TraceStep) -> None:
        bus.publish(
            "agent.trace",
            {"transactionId": tx.transaction_id, **step.model_dump(mode="json")},
        )

    started = time.perf_counter()
    bus.publish(
        "transaction.started",
        {
            "transactionId": tx.transaction_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "beneficiaryIsNew": tx.beneficiary_is_new,
            "principal": mandate.principal_id,
        },
    )

    supervisor = WakalahSupervisor(nac=_nac_client(), policy=_policy, on_trace=on_trace)
    state = await supervisor.evaluate(tx, mandate)
    if state.decision is None:  # pragma: no cover - graph always decides
        raise HTTPException(status_code=500, detail="no decision produced")

    decision = _recheck_mandate(tx, mandate, state)
    memory.decisions.put(decision)
    await audit.record_decision(decision, mandate)
    response = EvaluateResponse.from_decision(
        decision, latency_ms=int((time.perf_counter() - started) * 1000)
    )
    bus.publish("decision.final", response.model_dump(mode="json", by_alias=True))
    return response


@app.get("/v1/transactions/{transaction_id}", response_model=EvaluateResponse)
async def get_transaction(transaction_id: str) -> EvaluateResponse:
    decision = memory.decisions.get(transaction_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="transaction not found")
    return EvaluateResponse.from_decision(decision)


# ------------------------------------------------------------------- scenario
class _ApiBeatRunner(BeatRunner):
    """Executes beats by calling the service's own handlers.

    Deliberately goes through the real endpoints rather than shortcutting to the
    supervisor: what the audience sees is exactly what a partner integration
    would get.
    """

    async def execute(self, beat: Beat, engine: ScenarioEngine) -> BeatResult:
        if beat.kind == "mandate":
            mandate = await create_mandate(CreateMandateRequest(**beat.payload))
            engine.mandate_id = mandate.mandate_id
            return BeatResult(
                beat_id=beat.id,
                title=beat.title,
                ok=True,
                summary=f"Mandate {mandate.mandate_id} for '{mandate.principal_id}'",
                detail={
                    "mandateId": mandate.mandate_id,
                    "principal": mandate.principal_id,
                    "amountLimit": mandate.amount_limit,
                },
            )

        if beat.kind == "operator_event":
            if engine.mandate_id is None:
                return BeatResult(beat.id, beat.title, False, NO_MANDATE_YET)
            mandate = await revoke_mandate(
                engine.mandate_id, beat.payload.get("reason", "sim_swap")
            )
            return BeatResult(
                beat_id=beat.id,
                title=beat.title,
                ok=mandate.status == MandateStatus.REVOKED.value,
                summary=f"Mandate {mandate.mandate_id} revoked ({beat.payload.get('reason')})",
                detail={"mandateId": mandate.mandate_id, "status": mandate.status},
            )

        # transaction beats
        payload = dict(beat.payload)
        compromised = payload.pop("useCompromisedPersona", False)
        unavailable = payload.pop("useUnavailablePersona", False)

        mandate_id = engine.mandate_id
        if compromised or unavailable:
            msisdn = COMPROMISED_MSISDN if compromised else UNAVAILABLE_MSISDN
            alt = await create_mandate(
                CreateMandateRequest(
                    principal_msisdn=msisdn,
                    agent_id="agent_rasheed_clone" if compromised else "agent_rasheed",
                    agent_key_fingerprint="fp_clone" if compromised else "fp_rasheed_ed25519",
                    amount_limit=2000,
                    beneficiary_ids=[],
                )
            )
            mandate_id = alt.mandate_id
        if mandate_id is None:
            return BeatResult(beat.id, beat.title, False, "No mandate yet — run 'mandate' first")

        decision = await evaluate_transaction(EvaluateRequest(mandate_id=mandate_id, **payload))
        return BeatResult(
            beat_id=beat.id,
            title=beat.title,
            ok=True,
            summary=(
                f"{decision.decision.upper()} (tier {decision.risk_tier}), "
                f"{len(decision.evidence_summary)} signals"
            ),
            detail={
                "decision": decision.decision,
                "riskTier": decision.risk_tier,
                "reasonCodes": decision.reason_codes,
                "agentProposal": decision.agent_proposal,
                "policyOverrodeAgent": decision.policy_overrode_agent,
                "signals": list(decision.evidence_summary),
            },
        )


@app.get("/v1/scenario")
async def scenario_status() -> dict[str, Any]:
    """The script, and how far through it we are."""
    return scenario.status()


@app.post("/v1/scenario/reset")
async def scenario_reset() -> dict[str, Any]:
    scenario.reset()
    return scenario.status()


@app.post("/v1/scenario/beats/{beat_id}")
async def scenario_run_beat(beat_id: str) -> dict[str, Any]:
    """Run one beat — the presenter's remote."""
    try:
        result = await scenario.run(beat_id, _ApiBeatRunner())
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown beat: {beat_id}") from None
    return result.__dict__


@app.post("/v1/scenario/run-all")
async def scenario_run_all() -> dict[str, Any]:
    """Run the whole story — for rehearsals and pre-demo checks."""
    results = await scenario.run_all(_ApiBeatRunner())
    return {"results": [r.__dict__ for r in results]}


# --------------------------------------------------------------------- stream
@app.websocket("/ws")
async def websocket_stream(websocket: WebSocket) -> None:
    """Live event stream: nac.call, agent.trace, decision.final, mandate.*.

    A late-joining client is sent the recent buffer first, so the demo story is
    not lost if the UI reconnects mid-run.
    """
    await websocket.accept()
    queue = bus.subscribe()
    try:
        for event in bus.recent():
            await websocket.send_json(event)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=20.0)
            except TimeoutError:
                await websocket.send_json({"type": "ping", "ts": utc_now().isoformat()})
                continue
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(queue)


def _recheck_mandate(tx: TransactionRequest, mandate: Mandate, state: Any) -> Any:
    """Re-read the mandate after evidence gathering, before committing.

    Gathering signals takes seconds, and a revocation can arrive inside that
    window — which is exactly the case Wakalah exists for. Re-deciding against
    the mandate's current state is what makes "revoked mid-transaction" real
    rather than a story: the evidence is already in hand, so this is one cheap
    deterministic pass, not another round of network calls.
    """
    decision = state.decision
    current = memory.mandates.get(tx.mandate_id)
    if current is None or current.status is mandate.status:
        return decision

    revised = _policy.decide(
        tx,
        current,
        state.evidence,
        agent_tier=state.agent_tier,
        agent_proposal=state.agent_proposal,
        agent_rationale=state.agent_rationale,
    )
    bus.publish(
        "mandate.changed_mid_flight",
        {
            "transactionId": tx.transaction_id,
            "statusAtStart": mandate.status.value,
            "statusNow": current.status.value,
            "verdictBefore": decision.verdict.value,
            "verdictNow": revised.verdict.value,
        },
    )
    return revised


def _mandate_response(mandate: Mandate) -> MandateResponse:
    return MandateResponse(
        mandate_id=mandate.mandate_id,
        principal_id=mandate.principal_id,
        agent_id=mandate.agent_id,
        status=mandate.status.value,
        amount_limit=mandate.scope.amount_limit,
        currency=mandate.scope.currency,
        beneficiary_ids=mandate.scope.beneficiary_ids,
        created_at=mandate.created_at.isoformat(),
    )
