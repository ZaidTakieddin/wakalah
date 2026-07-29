# 07 — Repo Conventions, Backend Blueprint, Frontend Contract

## 1. Repo conventions

```
backend/     Zaid — service, agents, policy, NaC integration
frontend/    teammate — demo UI + API-call panel + video capture
docs/        shared — this suite, tooling guide, submission drafts
README.md    workspace index
.env.example never real keys; real .env is git-ignored
```

- **Commit hygiene from day 1**: small commits, real messages, both members committing throughout — the history *is* our originality evidence for the judges (rule: developed entirely within Jul 1–Sep 13).
- **No secrets in git, ever**: RapidAPI/NaC keys via env only. If a key leaks into history, rotate it — don't just delete the line.
- Branches: `main` always demoable after W3; feature branches merge via PR (even in a 2-person team — it's our review moment).
- `SYNTHETIC_DATA.md` at root once the demo exists (honesty ledger — see concept doc §6).

## 2. Backend blueprint (concept-agnostic core — safe to build before the Jul 12 gate)

**Stack:** Python 3.12 + FastAPI + WebSockets. Rationale: NaC ships a Python SDK, every plausible tooling-guide agent stack is Python-first, and one process serves both REST and the WS event stream. (Swap only if the Tooling Guide forces it.)

```
backend/
  app/
    main.py              FastAPI app: WS endpoint + REST routes
    nac/
      client.py          NacClient interface (the abstraction that survives the gate)
      sdk_impl.py        impl via NaC Python SDK / REST
      mcp_impl.py        impl via NaC MCP (if connector works)
      replay.py          record/replay cache of real responses  ← live-demo fallback A
    agents/              ★ AI agent component — approved tools ONLY (tooling guide)
      orchestrator.py
      ...                (post-gate: risk/planner/rescue  OR  mandate/sentinel/scorer)
    policy/              deterministic core — NOT the AI component
      engine.py          hard gates (statute thresholds / token validity rules)
      rules_*.yaml       human-readable policy, versioned
    scenario/
      clock.py           simulation clock; deterministic timeline driver
      events.py          scripted + injected events (incl. synthetic WBGT feed for MIZAN)
    models/
      events.py          pydantic schemas for every WS event (the frontend contract)
      domain.py          permits/tokens, workers/principals, zones/mandates
    store/
      *.py               repository modules — the ONLY place that touches Supabase
    audit/
      log.py             every agent decision + evidence refs; export endpoint
  supabase/
    migrations/          numbered SQL files; append-only, never edit past ones
  tests/
```

Design rules:
1. **`NacClient` is the only door to the network.** Agents get it as a tool; nothing else imports the SDK. Swapping SDK↔MCP↔replay is a constructor argument.
2. **Agents propose, `policy/` disposes.** The deterministic engine has final authority; agent output is a *proposal* object that policy accepts/rejects. This is both the safety story for judges and the tooling-compliance boundary (agents = restricted component; policy = conventional code). Confirm the boundary reading against the guide (doc 02 §3).
3. **Everything observable is an event.** Agents, policy, and NaC calls all emit typed events onto one bus → WS broadcast + audit log get the same truth. The UI's live API-call panel is just a renderer of `nac.call` events.
4. **The demo is a timeline, not luck.** `scenario/` replays a scripted event sequence against the real NaC simulators; same run every time. Rehearsals with `replay` recording on produce fallback data automatically.
5. **Storage = Supabase (adopted Jul 7, D18), server-side only.** Tables: principals, mandates, tokens, verifications (the audit trail), nac_calls. Access exclusively through `app/store/` repositories via supabase-py with the **service key** in `backend/.env` — the frontend never talks to Supabase; it speaks only the FastAPI WS/REST contract. Schema lives in `supabase/migrations/`. Code-quality rules for all of this: [backend/CLAUDE.md](../backend/CLAUDE.md) + `backend/pyproject.toml` (ruff, mypy, pytest gates).

## 3. Frontend contract (start building against this today)

Transport: one WebSocket (`/ws`) broadcasting JSON events `{type, ts, payload}`; REST for control. Mock server note: until the backend exists, frontend can replay a static JSON array of these events on a timer — the schema is the contract.

**WS events (concept-agnostic):**

| type | payload | UI use |
|---|---|---|
| `state.snapshot` | full domain state | initial render / resync |
| `nac.call` | `{api, operation, request, response, latency_ms, simulated}` | **live API-call panel** (the judges' proof) |
| `agent.decision` | `{agent, decision, rationale, evidence_refs[]}` | decision feed / toasts |
| `policy.verdict` | `{proposal_id, verdict: approved\|rejected, rule}` | "AI proposes, policy disposes" moment |
| `incident.updated` | `{id, severity, stage, subject}` | incident console |

**MIZAN-specific:** `zone.updated {id, wbgt, risk}` · `worker.updated {id, zone, exposure_min, status}` · `permit.updated {id, task, status: active|revoked|deferred, reason}` · `plan.proposed {changes[]}` / `plan.applied` — map + permit board + the APPLY SAFE PLAN button.

**Wakalah-specific:** `mandate.updated {id, principal, agent, scope, status}` · `token.verified {token_id, verdict, signals}` · `token.revoked {token_id, cause}` · `tx.updated {id, agent, amount, status}` — split-screen consumer views + trust dashboard.

**REST:**

| Route | Purpose |
|---|---|
| `GET /state` | snapshot (same shape as `state.snapshot`) |
| `POST /scenario/start` · `/pause` · `/reset` | demo control |
| `POST /scenario/inject` | fire a named event (e.g. `red_zone_entry`, `sim_swap_attack`) — the presenter's remote |
| `POST /plan/apply` (MIZAN) / `POST /verify` (Wakalah) | the two "button" moments in the demos |

## 3.5 Partner-facing API contract (adopted Jul 14, D25 — the shape the backend implements)

Two audiences, do not confuse them: §3 above is the **demo UI contract** (WebSocket + scenario control). This section is the **product contract** — what a bank, PSP, or merchant integrates against. Principle from the external review: *expose business intents, not raw telco quirks.* The partner asks "should this transaction proceed?"; Wakalah decides internally which CAMARA signals to pull.

| Route | Purpose |
|---|---|
| `POST /v1/link-sessions` | Start mandate creation: kicks off the operator consent flow (NV) + returns a redirect/capture instruction |
| `POST /v1/transactions/evaluate` | **The main endpoint.** Partner submits a transaction; Wakalah returns `allow` / `challenge` (STEP-UP) / `deny` with reason codes and an evidence summary |
| `POST /v1/transactions/{id}/confirm` | Completes a challenged transaction after step-up proof |
| `GET  /v1/transactions/{id}` | Decision + audit reference lookup |
| `POST /v1/consents/check` | Consent/purpose status for a principal (production-facing; stubbed in the demo) |

**Evaluate response shape** (the demo dashboard renders exactly this):

```json
{ "transactionId": "tx_…", "decision": "challenge",
  "reasonCodes": ["DEVICE_SWAP_RECENT", "AMOUNT_ABOVE_PARTNER_THRESHOLD"],
  "riskTier": "high",
  "evidenceSummary": { "numberVerification": "not_yet_performed",
                       "simSwap": {"status": "not_recent"},
                       "deviceSwap": {"status": "recent", "maxAgeHours": 24} },
  "challenge": { "challengeId": "chl_…", "method": "step_up_number_verification" } }
```

`reasonCodes` are stable machine-readable strings (not prose) so partners can build rules on them — and they double as the human-readable "why" in the demo UI.

**Normalized internal evidence schema — `app/nac/` emits only this shape, never raw provider JSON.** This is what keeps the policy engine independent of operator/provider differences, and it carries the compliance context every regulator asks about:

```json
{ "signal": "sim_swap", "provider": "nokia_nac", "network": "operator_x",
  "subject": {"phoneNumber": "+99999991000"},
  "result": {"recent": false, "latestTimestamp": "2026-07-14T12:03:21Z"},
  "purpose": "FraudPreventionAndDetection",
  "legalBasis": "legitimate_interest",
  "consentStatus": "not_required_at_runtime",
  "evidenceTime": "2026-07-14T15:32:11Z",
  "source": "live" }
```

`source` ∈ `live | cached | replay | simulated` — this single field powers the honesty labelling in the UI (doc 04 §5). `purpose` / `legalBasis` / `consentStatus` exist because real operators differ per market (Orange FR runs SIM-swap fraud checks on *legitimate interest*; other markets require explicit runtime consent) — carrying them from day one is what makes the design production-credible.

## 4. Definition of done — demo backend

- [ ] Scenario runs start→finish unattended in <3 min, emitting all storyboard beats (concept doc §7/§6)
- [ ] Every storyboard NaC call is a **real simulator call** visible as `nac.call` events
- [ ] Replay mode produces an identical run with network unplugged
- [ ] Audit export returns a readable decision log for the run
- [ ] `pytest` covers: policy gates, scenario determinism, NacClient replay parity
