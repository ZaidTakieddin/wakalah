# 10 — Frontend Integration Guide

*For Yasser. Everything needed to build the demo UI against the Wakalah backend: how to run it, every endpoint, every live event, and — the part that matters most — how the data should be presented.*

---

## 1. Quick start

**Terminal 1 — backend** (from `backend/`):
```
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload
```
Check it: <http://127.0.0.1:8000/health> · interactive API docs: <http://127.0.0.1:8000/docs>

**Terminal 2 — frontend** (from `frontend/`):
```
npm install
npm run dev
```

CORS is already open for any origin, so the Vite dev server works with no proxy.

**You do not need any API keys.** Everything (Nokia CAMARA, Gemini, Supabase) is called by the backend using Zaid's `backend/.env`. The frontend only ever talks to `http://127.0.0.1:8000`.

---

## 2. What you are building, in one minute

An AI agent asks to move money on a human's behalf. Wakalah decides whether to **allow**, **challenge**, or **deny**, using live signals from the mobile network (was the SIM swapped? are calls being forwarded? did the subscriber behind this number change?).

Two things happen on every request, and **the UI's whole job is to make them visible**:

1. **An AI agent reasons** — it classifies risk, *chooses which checks to run*, reads the results, and proposes a verdict.
2. **A deterministic policy engine decides** — it can overrule the agent, and it enforces a minimum set of checks the agent cannot skip.

> The single most important thing to show on screen: **the agent's plan changes with risk.** A routine payment gets 1 check; a large transfer to a new beneficiary gets 7–8. That visible difference is what the judges score under "Agentic AI & Multi-API Orchestration."

---

## 3. ⚠️ The one constraint that shapes your whole design

**A decision takes 5–25 seconds.** Three LLM calls plus up to eight network calls. That is normal and expected.

**Never show a spinner for 20 seconds.** Instead, subscribe to the WebSocket and render each step as it arrives. The wait *is* the show: the audience watches the agent think.

```
[✓] classify_risk    gemini   6.1s   Risk classified HIGH
[✓] build_plan       gemini   5.2s   Agent planned 5 checks
[✓] enforce_floor             —      Policy floor added 2 checks
[⟳] gather_evidence           …      calling 7 signals
```

---

## 4. REST API

Base URL: `http://127.0.0.1:8000` · JSON in, JSON out · all field names **camelCase**.

### `GET /health`
Use it for a connection indicator and to show which AI brains are live.
```json
{
  "status": "ok",
  "nac_mode": "live",
  "policy_version": "v1",
  "brains_configured": ["gemini", "gemini_fast", "groq", "ollama"],
  "audit_backend": "supabase",
  "mandates": 1,
  "decisions": 3,
  "ws_subscribers": 1
}
```
`audit_backend` may read `"memory (supabase unavailable: …)"` — that's the graceful-degradation path, worth surfacing as a small badge rather than hiding.

### `POST /v1/mandates` → 201
Creates the authorization ("wakalah contract"). Leave `principalName` out and the operator's registered identity is filled in automatically via CAMARA KYC Fill-in.
```jsonc
// request
{
  "principalMsisdn": "+99999991001",
  "agentId": "agent_rasheed",
  "agentKeyFingerprint": "fp_rasheed_ed25519",
  "amountLimit": 2000,
  "currency": "QAR",
  "beneficiaryIds": ["ben_mother", "ben_landlord"]
}
// response
{
  "mandateId": "man_0001",
  "principalId": "Arjona",          // ← autofilled by the operator
  "agentId": "agent_rasheed",
  "status": "active",
  "amountLimit": 2000,
  "currency": "QAR",
  "beneficiaryIds": ["ben_mother", "ben_landlord"],
  "createdAt": "2026-08-06T12:50:24.123456+00:00"
}
```

### `POST /v1/transactions/evaluate` → 200 — **the main call**
```jsonc
// request
{
  "transactionId": "tx_demo_1",        // unique per request
  "mandateId": "man_0001",
  "amount": { "value": 1500, "currency": "QAR" },
  "beneficiaryId": "ben_landlord",
  "beneficiaryIsNew": true
}
```
```jsonc
// response (real capture)
{
  "transactionId": "tx_demo_1",
  "decision": "challenge",             // "allow" | "challenge" | "deny"
  "riskTier": "high",                  // "low" | "medium" | "high"
  "reasonCodes": ["AGENT_REQUESTED_STEP_UP"],
  "rationale": "no rule fired, but the agent asked for additional verification | agent: …",
  "evidenceSummary": {
    "sim_swap": {
      "dimension": "hijack",
      "result": { "swapped": false },
      "source": "live",                // live | cached | replay | simulated | unavailable
      "available": true,
      "errorCode": null
    },
    "call_forwarding": {
      "dimension": "hijack",
      "result": { "forwarding_active": false },
      "source": "live", "available": true, "errorCode": null
    }
    // …one entry per signal checked
  },
  "challenge": { "challengeId": "chl_tx_demo_1", "method": "step_up_number_verification" },
  "policyVersion": "v1",
  "agentProposal": "challenge",        // what the AI proposed, BEFORE policy
  "policyOverrodeAgent": false,        // ← show this when true
  "decidedAt": "2026-08-06T12:50:24+00:00",
  "latencyMs": 20936
}
```

### Other endpoints

| Route | Use |
|---|---|
| `GET /v1/transactions/{id}` | re-fetch a past decision (same shape) |
| `GET /v1/mandates` | list mandates |
| `POST /v1/mandates/{id}/revoke?reason=sim_swap_detected` | fire the Sentinel revocation |
| `GET /v1/principals/{msisdn}/history` | audit trail for one principal |
| `GET /v1/scenario` | the demo script + progress |
| `POST /v1/scenario/beats/{beatId}` | run one beat — **the presenter's remote** |
| `POST /v1/scenario/run-all` | rehearsal |
| `POST /v1/scenario/reset` | start the story over |

`GET /v1/principals/{msisdn}/history` returns `principalRef` — a SHA-256 hash, not the number. Show the hash; it's a privacy feature worth pointing at.

---

## 5. WebSocket — the live stream

Connect to **`ws://127.0.0.1:8000/ws`**. Every message:
```ts
{ type: string, ts: string /* ISO */, payload: object }
```

On connect you receive a **replay of recent events** so a refresh mid-demo doesn't lose the story. A `ping` arrives every 20s — ignore it, or use it as a liveness dot.

### Event catalogue

| `type` | When | Key payload fields | Render as |
|---|---|---|---|
| `scenario.beat.started` | a demo beat begins | `id`, `title`, `narration`, `expect`, `labels[]` | the narration card / caption |
| `transaction.started` | evaluation begins | `transactionId`, `amount`, `currency`, `beneficiaryIsNew`, `principal` | open the decision panel |
| `agent.trace` | each agent/policy step | `step`, `summary`, `detail`, `brain`, `degraded`, `latencyMs` | **the reasoning trace** |
| `nac.call` | every network call | `signal`, `path`, `request`, `response`, `status`, `latencyMs`, `source`, `simulatedDevice` | **the live API panel** |
| `decision.final` | verdict ready | the whole `EvaluateResponse` | the verdict card |
| `mandate.updated` | mandate created | `mandateId`, `status`, `identityAutofilledByOperator` | mandate card |
| `mandate.revoked` | Sentinel fires | `mandateId`, `reason`, `status` | **the revocation moment** |
| `mandate.changed_mid_flight` | revoked *during* evaluation | `statusAtStart`, `statusNow`, `verdictBefore`, `verdictNow` | a dramatic override banner |
| `scenario.beat.finished` | beat done | `beatId`, `ok`, `summary`, `detail` | tick the beat in the timeline |
| `scenario.reset` | story reset | `beats[]` | clear the stage |

### `agent.trace` steps, in order

| `step` | `summary` example | Meaning |
|---|---|---|
| `classify_risk` | "Risk classified HIGH" | AI · `detail.agentTier` vs `detail.policyBaseline` |
| `build_plan` | "Agent planned 5 checks" | AI · `detail.signals[]`, `detail.rationale` |
| `enforce_floor` | "Policy floor added 2 check(s)" | **POLICY** · `detail.addedByPolicy[]`, `detail.finalPlan[]` |
| `gather_evidence` | "7/7 signals returned" | tools · `detail.results`, `detail.dimensionsCovered[]` |
| `interpret` | "Agent proposes STEP_UP" | AI · `detail.rationale`, `detail.concerns[]` |
| `decide` | "POLICY DENY (overrode agent STEP_UP)" | **POLICY** · `detail.policyOverrodeAgent` |

**Colour AI steps and POLICY steps differently.** That visual split is the architecture argument — the audience should see reasoning and authority alternate.

---

## 6. TypeScript types (copy-paste)

```ts
export type Decision = "allow" | "challenge" | "deny";
export type RiskTier = "low" | "medium" | "high";
export type EvidenceSource = "live" | "cached" | "replay" | "simulated" | "unavailable";
export type Dimension = "binding" | "identity" | "hijack" | "continuity" | "context";

export interface SignalEvidence {
  dimension: Dimension;
  result: Record<string, unknown>;
  source: EvidenceSource;
  available: boolean;
  errorCode: string | null;
}

export interface EvaluateResponse {
  transactionId: string;
  decision: Decision;
  riskTier: RiskTier;
  reasonCodes: string[];
  rationale: string;
  evidenceSummary: Record<string, SignalEvidence>;
  challenge: { challengeId: string; method: string } | null;
  policyVersion: string;
  agentProposal: Decision | null;
  policyOverrodeAgent: boolean;
  decidedAt: string;
  latencyMs: number | null;
}

export interface TraceStep {
  step: "classify_risk" | "build_plan" | "enforce_floor"
      | "gather_evidence" | "interpret" | "decide";
  summary: string;
  detail: Record<string, any>;
  brain: string | null;      // "gemini" | "gemini_fast" | "ollama" | "heuristic"
  degraded: boolean;         // true = no LLM answered, rules stood in
  latencyMs: number | null;
}

export interface WsEvent<T = any> { type: string; ts: string; payload: T; }
```

Minimal hook:
```ts
export function useWakalahStream(onEvent: (e: WsEvent) => void) {
  useEffect(() => {
    let socket: WebSocket;
    let retry: number;
    const connect = () => {
      socket = new WebSocket("ws://127.0.0.1:8000/ws");
      socket.onmessage = (m) => {
        const event = JSON.parse(m.data) as WsEvent;
        if (event.type !== "ping") onEvent(event);
      };
      socket.onclose = () => { retry = window.setTimeout(connect, 1500); };
    };
    connect();
    return () => { clearTimeout(retry); socket?.close(); };
  }, [onEvent]);
}
```

---

## 7. How the data should appear — the UI design

### Layout: three zones, always visible

```
┌──────────────────────────────────────────────────────────────────────┐
│  HEADER  Wakalah · connection dot · brains: gemini · audit: supabase  │
├────────────────────────────────┬─────────────────────────────────────┤
│  ① THE STORY                   │  ③ LIVE NETWORK CALLS               │
│  narration + beat timeline     │  every CAMARA call as it happens    │
│                                │  (this is the proof it's real)      │
│  ② THE DECISION                │                                     │
│  reasoning trace → verdict     │                                     │
└────────────────────────────────┴─────────────────────────────────────┘
```

Zone ③ stays on screen permanently. It is the single most persuasive element you can show a Nokia/GSMA judge: *real API calls, scrolling live.*

### ① The story panel

Driven by `scenario.beat.started`. Show `title`, `narration`, and — importantly — **`expect`** ("what to watch for"). Render `labels[]` as small muted chips: *"simulated operator event"*, *"real CAMARA calls"*. Below it, a timeline of the 7 beats with the current one highlighted; fetch from `GET /v1/scenario`.

### ② The reasoning trace — your centrepiece

Append one row per `agent.trace` event, animating in (framer-motion is perfect here):

```
🧠 classify_risk     [gemini · 6.1s]   Risk classified HIGH
   └ agent: high · policy baseline: high
🧠 build_plan        [gemini · 5.2s]   Agent planned 5 checks
   └ sim_swap, device_swap, call_forwarding, number_recycling, tenure
⚖️ enforce_floor                       Policy floor added 2 checks
   └ + reachability, location_verification
🔌 gather_evidence   [1.9s]            7/7 signals returned
🧠 interpret         [gemini · 7.0s]   Agent proposes DENY
⚖️ decide                              POLICY DENY
```

Rules:
- **🧠 AI steps and ⚖️ POLICY steps must look different** (colour + icon). This is the architecture, visible.
- Show `brain` as a small chip. If `degraded: true`, chip reads **"fallback rules"** in amber — honest, and it demonstrates graceful degradation rather than hiding it.
- `enforce_floor` with `addedByPolicy.length > 0` deserves emphasis: *the policy added checks the agent didn't plan.*

### The verdict card (`decision.final`)

```
        ╔═══════════════════════════════╗
        ║   ⛔  DENY                     ║
        ║   risk tier: HIGH             ║
        ╚═══════════════════════════════╝
   Agent proposed: STEP-UP  →  Policy: DENY   [POLICY OVERRODE AGENT]

   Why:  NUMBER_RECYCLED · SIM_SWAP_RECENT_HIGH_VALUE
         DEVICE_SWAP_RECENT · CALL_FORWARDING_ACTIVE
```

- Colours: **allow** green · **challenge** amber · **deny** red.
- When `policyOverrodeAgent` is true, show the agent's proposal *next to* the verdict with an arrow. **This is the "AI proposes, policy disposes" moment** — don't bury it.
- Turn `reasonCodes` into human sentences, but keep the code visible (partners build on the codes):
  `SIM_SWAP_RECENT_HIGH_VALUE` → *"SIM swapped recently, on a high-value transfer"*.

### Signal cards (`evidenceSummary` / `nac.call`)

One card per signal, **grouped by the five trust dimensions**:

```
HIJACK          IDENTITY       CONTINUITY        CONTEXT
┌────────────┐  ┌───────────┐  ┌─────────────┐  ┌──────────────┐
│ SIM Swap   │  │ KYC Match │  │ Recycling   │  │ Reachability │
│ ⚠ swapped  │  │ …         │  │ ⚠ changed   │  │ ✓ reachable  │
│ live · 0.9s│  │           │  │ live · 0.5s │  │ live · 1.1s  │
└────────────┘  └───────────┘  └─────────────┘  └──────────────┘
```

The dimension grouping is worth the effort: it turns "we called ten APIs" into "we answer five different questions." Read `dimension` straight off each `SignalEvidence`.

Card states: **green** = clean · **red/amber** = risk found · **grey with error code** = `available: false`.

### 🔒 Honesty labels — non-negotiable

Every signal carries `source`. **Render it on every card, always:**

| `source` | Chip |
|---|---|
| `live` | 🟢 **LIVE** |
| `cached` / `replay` | 🔵 **CACHED** (recorded real response) |
| `simulated` | 🟡 **SIMULATED** |
| `unavailable` | ⚪ **UNAVAILABLE** + error code |

This is not decoration — it is a scored honesty feature and the reason judges will trust everything else on the screen. Never render a cached or simulated value as if it were live.

### ③ The live API panel (`nac.call`)

An append-only log, newest at the bottom, auto-scrolling:
```
POST /passthrough/camara/v1/sim-swap/sim-swap/v0/check      200   0.9s  live
     → {"swapped": false}
POST /device-status/device-reachability-status/v1/retrieve  200   1.1s  live
     → {"reachable": true, "connectivity": ["DATA"]}
```
Show method, path, status, latency, and the response. Colour non-2xx amber — a `503` from the error-simulator persona is a *feature* in the degraded beat, not something to hide.

### The revocation moment (`mandate.revoked`, `mandate.changed_mid_flight`)

This is the demo's dramatic peak. Make it loud: full-width red banner, brief shake or flash, mandate card flipping `active → revoked`. If `mandate.changed_mid_flight` arrives, show *"verdict changed mid-transaction: ALLOW → DENY"* — that's revocation landing while the decision was still being made.

---

## 8. Driving the demo

Give the presenter buttons — one per beat, in order, from `GET /v1/scenario`:

```
[1 Mandate] [2 Routine] [3 Step-up] [4 Out of scope]
[5 SIM swap!] [6 Cloned agent] [7 Degraded]        [Reset]
```

Each button = `POST /v1/scenario/beats/{id}`. The story then arrives over the WebSocket; the button just triggers it. Disable buttons while a beat is running, and tick them as `scenario.beat.finished` arrives.

Expected results (use these to check your rendering is right):

| Beat | Verdict | Signals | The point |
|---|---|---|---|
| `mandate` | — | KYC Fill-in | identity autofilled by the operator |
| `routine` | **ALLOW** | **1** | small plan for a routine payment |
| `stepup` | **CHALLENGE** | **7** | *the plan grew* |
| `out_of_scope` | **DENY** | 4 | mandate scope refuses it |
| `hijack_event` | — | — | revocation, machine-to-machine |
| `cloned_agent` | **DENY** | **8** | 4 hijack/continuity reason codes |
| `degraded` | **CHALLENGE** | 4 | missing evidence never means approved |

**If you build one thing well, make it the contrast between `routine` (1 check) and `cloned_agent` (8 checks).** Consider keeping the previous beat's plan visible so the growth is literally side by side.

---

## 9. Practical notes

- **Latency**: 5–25s per decision. Stream; never block on the POST alone.
- **Two clients, one story**: you can fire `evaluate` from a button *and* receive its events on the WebSocket. Match them with `transactionId`.
- **Reconnect**: the socket replays recent events, so a refresh recovers the story. Always auto-reconnect.
- **`transactionId` must be unique** per request, or you'll overwrite a stored decision.
- **Errors**: `404` = unknown mandate/transaction; `422` = malformed body (check camelCase). Surface the FastAPI `detail` string.
- **Personas** (fixed behaviour, useful for testing): `+99999991001` clean · `+99999991000` compromised · `+99999990503` always fails.
- **Explore freely** at <http://127.0.0.1:8000/docs> — try requests there before wiring them.

## 10. Suggested build order

1. Health badge + WebSocket connection dot — proves the wiring.
2. The **live API panel** — pure `nac.call` rendering, immediately impressive.
3. The **reasoning trace** — `agent.trace`, with AI/POLICY styling.
4. The **verdict card** — including the agent-vs-policy comparison.
5. **Signal cards** grouped by dimension, with honesty chips.
6. The **beat buttons** + narration panel.
7. The **revocation** dramatics.

Steps 2–4 alone make a compelling demo. Everything after is polish that raises the score.
