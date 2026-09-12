# 10 — Frontend Integration Guide

*For Yasser. Everything needed to build the demo UI against the Wakalah backend: how to run it, every endpoint, every live event, and — the part that matters most — how the data should be presented.*

---

## 1. Quick start

**Terminal 1 — backend** (from `backend/`):
```
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload
```
Check it: <http://127.0.0.1:8000/health> · interactive API docs: <http://127.0.0.1:8000/docs>

**Terminal 2 — frontend.** The demo app lives on branch `yasser`, in `wakalah-balance-demo/` (Next.js + React 19 + Tailwind 4):
```
git switch yasser           # or merge it into main first
cd wakalah-balance-demo
npm install
npm run dev                 # .env.local: WAKALAH_API_BASE=http://127.0.0.1:8000
```
Against the **hosted** backend (Render) instead of localhost, point both variables at it — Vercel env dashboard or `.env.local`:
```
WAKALAH_API_BASE=https://<backend>.onrender.com
NEXT_PUBLIC_WAKALAH_WS_URL=wss://<backend>.onrender.com/ws
```
(`wss`, not `ws` — the host redirects plain WebSocket handshakes to TLS. Miss the second variable and REST works while the live stream silently stays on localhost.)

CORS is already open for any origin, so any dev server works with no proxy.

**You do not need any API keys.** Everything (Nokia CAMARA, Gemini, Supabase) is called by the backend using Zaid's `backend/.env`. The frontend only ever talks to `http://127.0.0.1:8000`.

---

## 2. What you are building, in one minute

An AI agent asks to move money on a human's behalf. Wakalah decides whether to **allow**, **challenge**, or **deny**, using live signals from the mobile network (was the SIM swapped? are calls being forwarded? did the subscriber behind this number change?).

Two things happen on every request, and **the UI's whole job is to make them visible**:

1. **An AI agent reasons** — it classifies risk, *chooses which checks to run*, reads the results, and proposes a verdict.
2. **A deterministic policy engine decides** — it can overrule the agent, and it enforces a minimum set of checks the agent cannot skip.

> The single most important thing to show on screen: **the agent's plan changes with risk.** A routine payment gets 1 check; a large transfer to a new beneficiary gets 4+ (policy-guaranteed floor, more if the agent adds). That visible difference is what the judges score under "Agentic AI & Multi-API Orchestration."

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
  "nac_mode": "replay",
  "policy_version": "v2",
  "brains_configured": ["gemini", "gemini_fast", "groq", "ollama"],
  "audit_backend": "supabase",
  "mandates": 1,
  "decisions": 3,
  "ws_subscribers": 1
}
```
`audit_backend` may read `"memory (supabase unavailable: …)"` — that's the graceful-degradation path, worth surfacing as a small badge rather than hiding. Two more honest-label notes: `nac_mode` is **`replay`** whenever the backend serves recorded responses (offline demo) — pair it with the 🔵 CACHED chips; and `brains_configured` lists what's *configured*, not what's *verified* — a dead brain shows up in events as `degraded` instead.

### `POST /v1/mandates` → 201
Creates the authorization ("wakalah contract"). Leave `principalName` out and the operator's registered identity is filled in automatically via CAMARA KYC Fill-in.
> In **replay mode** that autofill cannot run, so `principalId` arrives empty — render the MSISDN as the fallback label rather than an empty string.
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
// response (real capture, policy v2)
{
  "transactionId": "tx_demo_1",
  "decision": "challenge",             // "allow" | "challenge" | "deny"
  "riskTier": "medium",                // "low" | "medium" | "high"
  "reasonCodes": ["NEW_BENEFICIARY_MATERIAL_VALUE"],
  "rationale": "first payment to ben_landlord of 1500 QAR | agent: …",
  "evidenceSummary": {
    "sim_swap": {
      "dimension": "hijack",
      "result": { "swapped": false },
      "source": "replay",              // live | cached | replay | simulated | unavailable
      "available": true,
      "errorCode": null
    },
    "call_forwarding": {
      "dimension": "hijack",
      "result": { "forwarding_active": false },
      "source": "replay", "available": true, "errorCode": null
    }
    // …one entry per signal checked
  },
  "challenge": { "challengeId": "chl_tx_demo_1", "method": "step_up_number_verification" },
  "policyVersion": "v2",
  "agentProposal": "allow",            // what the AI proposed, BEFORE policy
  "policyOverrodeAgent": true,         // ← show this when true
  "decidedAt": "2026-08-22T17:50:24+00:00",
  "latencyMs": 20936
}
```

**Reason codes → human sentences** (keep the raw code visible; partners build on them):

| Code | Say |
|---|---|
| `MANDATE_NOT_ACTIVE` | mandate revoked or expired |
| `AMOUNT_EXCEEDS_MANDATE_LIMIT` | above what the principal authorized |
| `BENEFICIARY_NOT_PERMITTED` | outside the mandate's beneficiary list |
| `IDENTITY_MISMATCH` | claimed identity fails against operator records |
| `NUMBER_RECYCLED` | the subscriber behind this number changed |
| `SIM_SWAP_RECENT_HIGH_VALUE` | SIM swapped recently, on a high-value transfer (takeover pattern) |
| `NEW_BENEFICIARY_MATERIAL_VALUE` | first-ever payment to this beneficiary at material size |
| `SIM_SWAP_RECENT_LOW_VALUE` | recent SIM swap, smaller amount |
| `DEVICE_SWAP_RECENT` | same SIM in a new device recently |
| `CALL_FORWARDING_ACTIVE` | calls silently forwarded — possible OTP interception |
| `PRINCIPAL_CHALLENGE_ONLY` | principal under challenge-only after a hijack signal |
| `NUMBER_NOT_VERIFIED` / `DEVICE_UNREACHABLE` / `LOCATION_INCONSISTENT` | binding/reachability/context check failed |
| `INSUFFICIENT_EVIDENCE` | required checks could not be completed — never auto-approves |
| `AGENT_REQUESTED_STEP_UP` | no rule fired, but the AI asked for more verification |

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

`GET /v1/scenario` feeds the ribbon and timeline directly:
```jsonc
{
  "beats": [
    { "id": "routine", "title": "The monthly remittance", "narration": "…",
      "expect": "ALLOW, on a small plan", "labels": ["real CAMARA calls"], "done": true }
    // …seven beats, in story order
  ],
  "mandateId": "man_0001",
  "results": [ /* one BeatResult per beat already run */ ]
}
```

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
| `scenario.beat.started` | a demo beat begins | `beatId`, `title`, `narration`, `expect`, `labels[]` | the narration card / caption |
| `transaction.started` | evaluation begins | `transactionId`, `beatId`, `amount`, `currency`, `beneficiaryId`, `beneficiaryIsNew`, `principal` (name, may be empty), `msisdn` (the number — stream only, never stored) | open the decision panel |
| `agent.trace` | each agent/policy step | `transactionId`, `beatId`, `step`, `summary`, `detail`, `brain`, `degraded`, `latencyMs` | **the reasoning trace** |
| `nac.call` | every network call | `signal`, `path`, `request`, `response`, `status`, `latencyMs`, `source`, `simulatedDevice`, `transactionId`, `beatId` | **the live API panel** |
| `decision.final` | verdict ready | the whole `EvaluateResponse` (+ `beatId`, null outside beats) | the verdict card |
| `mandate.updated` | mandate created | `mandateId`, `status`, `identityAutofilledByOperator`, `beatId` (when in-beat) | mandate card |
| `mandate.revoked` | Sentinel fires | `mandateId`, `reason`, `status`, `beatId` (when in-beat) | **the revocation moment** |
| `mandate.changed_mid_flight` | revoked *during* evaluation | `transactionId`, `beatId`, `statusAtStart`, `statusNow`, `verdictBefore`, `verdictNow` | a dramatic override banner |
| `scenario.beat.finished` | beat done | `beatId`, `ok`, `summary`, `detail` | tick the beat in the timeline |
| `scenario.reset` | story reset | `beats[]` | clear the stage |

**Attribution rule (simple now):** every event inside a beat carries that beat's `beatId`; every event inside an evaluation carries its `transactionId`. No `beatId` = outside any beat; no `transactionId` on a `nac.call` = outside any evaluation (e.g. KYC Fill-in during mandate creation). Route runs by `transactionId`, group them under beats by `beatId` — no temporal guessing needed.

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
  beatId: string | null;   // set when decided inside a scenario beat
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

### The concept: a Trust Operations Console

Ask who would ever look at a Wakalah screen in production: a **fraud/risk analyst** at a bank, a **compliance officer**, an **integration engineer**. Never a consumer — the consumer's agent transacts while they sleep, which is the whole premise.

So the honest UI is an **operations console**, in the family of Stripe Radar or Sift. That is also the most persuasive thing to put in front of judges: it looks like something a bank could buy, not a hackathon toy.

> ❌ **Not a chatbot.** A chat box where a human types *"send 100 QAR to Ben"* files us under "AI banking assistant" — a commodity category — and quietly contradicts our own problem statement (*the human isn't there*). Human context belongs in the scenario narration, not a fake conversation.

### The layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ WAKALAH · Trust Layer for AI-Agent Transactions   ● live  brain:gemini  ⛁ db │
├──────────────────────────────────────────────────────────────────────────────┤
│ ▸ SCENARIO   ①mandate ②routine ③step-up ④out-of-scope ⑤SIM SWAP ⑥clone ⑦outage│
│   "The fraudster's copy of the agent asks for a large transfer…"              │
├──────────────────────────────────────────────────────────────────────────────┤
│ INCOMING REQUEST                                                              │
│   agent_rasheed_clone  →  1,800 QAR  →  ben_attacker      ⚠ NEW BENEFICIARY   │
│   mandate man_0001 · limit 2,000/mo · principal Arjona · status REVOKED       │
├──────────────────────────────────────────────────────────────────────────────┤
│ DECISION PIPELINE                                            checks run:  5   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │🧠CLASSIFY│▸│🧠 PLAN  │▸│⚖ FLOOR  │▸│🔌GATHER │▸│🧠INTERP │▸│⚖ DECIDE │    │
│  │  MEDIUM │ │3 checks │ │ +2 added│ │  5/5    │ │CHALLENGE│ │  DENY   │    │
│  │ gemini  │ │ gemini  │ │ policy  │ │  1.9s   │ │ gemini  │ │ policy  │    │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘    │
│  ▸ "large transfer to an unknown beneficiary on a line with hijack signals"   │
├────────────────────────────────────────┬─────────────────────────────────────┤
│ EVIDENCE · 5 trust dimensions          │ LIVE CAMARA CALLS · Nokia NaC       │
│                                        │                                     │
│ HIJACK          ⚠ 3 findings           │ POST …/sim-swap/v0/check   200 0.9s │
│  ⚠ SIM Swap      swapped      🟢LIVE   │   → {"swapped": true}               │
│  ⚠ Device Swap   swapped      🟢LIVE   │ POST …/device-swap/check   200 0.8s │
│  ⚠ Forwarding    active       🟢LIVE   │   → {"swapped": true}               │
│                                        │ POST …/call-forwarding     200 1.2s │
│ CONTINUITY      ⚠ 1 finding            │   → {"active": true}                │
│  ⚠ Recycling     subscriber changed    │ …                                   │
│  ✓ Tenure        PAYG                  │                                     │
│                                        │                                     │
│ CONTEXT         ✓ clear                │                                     │
├────────────────────────────────────────┴─────────────────────────────────────┤
│  ⛔ DENY          agent proposed CHALLENGE → policy DENY [OVERRIDDEN]         │
│  NEW_BENEFICIARY_MATERIAL_VALUE · NUMBER_RECYCLED ·                           │
│  SIM_SWAP_RECENT_HIGH_VALUE · DEVICE_SWAP_RECENT · CALL_FORWARDING_ACTIVE     │
│                                     policy v2 · 12.4s · audited               │
├──────────────────────────────────────────────────────────────────────────────┤
│ RECENT   ✅ routine 1 check  │  ⚠️ step-up 4 checks  │  ⛔ clone 5 checks      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component 1 — Header

`GET /health` on load, plus the WebSocket state. Connection dot (green connected / amber reconnecting / red down), `brains_configured[0]`, and `audit_backend`. If `audit_backend` starts with `"memory"`, show an amber **DEGRADED** chip — surfacing graceful degradation is worth more than hiding it.

### Component 2 — Scenario ribbon

The presenter's remote *and* the human story, so no chat is needed.

- Beats from `GET /v1/scenario` → seven numbered buttons, `POST /v1/scenario/beats/{id}` on click.
- On `scenario.beat.started`: show `narration` as the caption, `expect` as a muted "watch for…" line, and `labels[]` as small chips (*"simulated operator event"*, *"real CAMARA calls"*).
- On `scenario.beat.finished`: tick the beat. Disable all buttons while a beat runs.

### Component 3 — Incoming request

From `transaction.started` plus the mandate. Show requesting `agentId`, amount, beneficiary, and a ⚠ chip when `beneficiaryIsNew`. Second line: mandate id, limit, principal, **status** — status flipping to `REVOKED` between beats 5 and 6 is a story beat in itself.

### Component 4 — Decision pipeline ⭐ the centrepiece

Six fixed nodes, filled in by `agent.trace` events in order:

| Node | `step` | Headline value | Sub-label |
|---|---|---|---|
| 🧠 CLASSIFY | `classify_risk` | `detail.agentTier` uppercased | `brain` |
| 🧠 PLAN | `build_plan` | `detail.signals.length` + " checks" | `brain` |
| ⚖ FLOOR | `enforce_floor` | `+N added` or `met` | `policy` |
| 🔌 GATHER | `gather_evidence` | `usable/total` | `latencyMs` |
| 🧠 INTERP | `interpret` | proposed verdict | `brain` |
| ⚖ DECIDE | `decide` | final verdict | `policy` |

Rules that carry the architecture:

- **🧠 AI nodes and ⚖ POLICY nodes must be visually distinct** — different colour and icon. The alternation *is* the "AI proposes, policy disposes" argument.
- Node states: `idle` (dim outline) → `running` (pulsing border) → `done` (filled). Advance on each event; the node that hasn't fired yet is the one pulsing.
- `enforce_floor` with `detail.addedByPolicy.length > 0` gets emphasis — *policy added checks the agent didn't plan*.
- `decide` with `detail.policyOverrodeAgent` gets a badge — *policy overrode the agent*.
- `degraded: true` on any node → amber **"fallback rules"** chip instead of the brain name.
- Below the row, show the current step's `detail.rationale` as one line of plain language.
- **`checks run: N`** in the corner, large. This number is the rubric point.

### Component 5 — Evidence, grouped by dimension

From `evidenceSummary` (and `nac.call` for live fill-in). Four groups in fixed order — **HIJACK · IDENTITY · CONTINUITY · CONTEXT** (BINDING appears at mandate time) — each with a header showing findings count.

Card states: **green ✓** clean · **amber/red ⚠** risk found · **grey** `available: false` with its `errorCode`.

The grouping is worth the effort: it turns "we called ten APIs" into "we answer five different questions."

### Component 6 — Live CAMARA log

Append-only, newest at the bottom, auto-scrolling, monospace. Method, path (truncate the long `/passthrough/camara/v1/…` prefix), status, latency, then the response on an indented line. Colour non-2xx amber — a `503` from the error-simulator persona is a *feature* in the outage beat.

**Keep this panel on screen permanently.** It is the single most persuasive element for a Nokia/GSMA judge: real API calls, scrolling live.

### Component 7 — Verdict bar

From `decision.final`. Large verdict, colour-coded (**allow** green · **challenge** amber · **deny** red). Beside it, when `policyOverrodeAgent` is true: `agent proposed X → policy Y` with an arrow. Then `reasonCodes` as chips — keep the raw code visible (partners build on them) with a human sentence on hover or beneath. Footer: `policyVersion`, `latencyMs`, and an "audited" marker.

### Component 8 — RECENT strip

The last three decisions: verdict icon, beat name, **check count**. This is the cheapest high-value component in the whole UI — `routine 1 check · step-up 4 · clone 5` makes the agent's judgment undeniable at a glance. **If you build one thing beyond the basics, build this.**

### Event → element map

| Event | Updates |
|---|---|
| `scenario.beat.started` | ribbon caption, labels; clear pipeline + evidence |
| `transaction.started` | incoming-request strip; pipeline → node 1 running |
| `agent.trace` | the matching pipeline node; rationale line; `checks run` |
| `nac.call` | live log row; evidence card fills in |
| `decision.final` | verdict bar; RECENT strip |
| `mandate.updated` / `mandate.revoked` | mandate status in the request strip |
| `mandate.changed_mid_flight` | override banner (see below) |
| `scenario.beat.finished` | tick the beat, re-enable buttons |
| `scenario.reset` | clear everything |

### Motion and timing

A decision takes **5–25 seconds**, and the pipeline is what turns that into theatre rather than dead air:

- Node transitions ~200ms ease-out; pulsing border on the running node (~1.2s loop).
- Log rows and evidence cards slide/fade in over ~150ms — enough to notice, not enough to annoy.
- The verdict bar arrives with a short scale-in; it should feel like a stamp landing.
- **Never a full-screen spinner.** If nothing has arrived for >30s, show a quiet "still working…" line rather than replacing the pipeline.

### Colour tokens (dark theme suits an ops console, and reads better on video)

| Token | Use |
|---|---|
| AI accent (e.g. violet) | 🧠 nodes, brain chips |
| Policy accent (e.g. cyan/slate) | ⚖ nodes, policy badges |
| Green | allow, clean signals, `LIVE` chip |
| Amber | challenge, degraded, cached/simulated, non-2xx |
| Red | deny, risk findings, revocation |
| Muted grey | unavailable signals, idle nodes |

### The revocation moment (`mandate.revoked`, `mandate.changed_mid_flight`)

The demo's dramatic peak. Full-width red banner, brief flash, mandate status flipping `active → REVOKED` in the request strip. On `mandate.changed_mid_flight`, show *"verdict changed mid-transaction: ALLOW → DENY"* — a revocation landing while the decision was still being made.

### What not to build

- **No chat box** — see the concept note above.
- **No free-text parsing/NLU** — it adds latency, a failure mode on stage, and makes us the assistant we say we aren't. Beat buttons are the input.
- **No consumer-app furniture** — avatars, message bubbles, "how can I help?". Wakalah is infrastructure; it should look like infrastructure.

### 🔒 Honesty labels — non-negotiable

Every signal carries `source`. **Render it on every card, always:**

| `source` | Chip |
|---|---|
| `live` | 🟢 **LIVE** |
| `cached` / `replay` | 🔵 **CACHED** (recorded real response) |
| `simulated` | 🟡 **SIMULATED** |
| `unavailable` | ⚪ **UNAVAILABLE** + error code |

This is not decoration — it is a scored honesty feature and the reason judges will trust everything else on the screen. Never render a cached or simulated value as if it were live.

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
| `stepup` | **CHALLENGE** | **4+** | *the plan grew* — first payment to a new beneficiary always steps up (policy v2) |
| `out_of_scope` | **DENY** | 4 | mandate scope refuses it |
| `hijack_event` | — | — | revocation, machine-to-machine |
| `cloned_agent` | **DENY** | **4+** | hijack AND continuity reason codes (`NUMBER_RECYCLED` included) |
| `degraded` | **CHALLENGE** | 3–4 | missing evidence never means approved |

Signal counts are floors-plus-agent: the deterministic layer guarantees these minimums every run; a bolder agent plan may add more.

**If you build one thing well, make it the contrast between `routine` (1 check) and `cloned_agent` (4–5 checks).** Consider keeping the previous beat's plan visible so the growth is literally side by side.

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

1. **Header** + WebSocket connection dot — proves the wiring end to end.
2. **Live CAMARA log** (component 6) — pure `nac.call` rendering. Easiest win, instantly impressive.
3. **Decision pipeline** (component 4) — the centrepiece, with 🧠/⚖ styling and node states.
4. **Verdict bar** (component 7) — including the agent-vs-policy comparison.
5. **Evidence cards** grouped by dimension (component 5), honesty chip on every one.
6. **Scenario ribbon** + beat buttons (component 2) and the **incoming request** strip (component 3).
7. **RECENT strip** (component 8) — cheap, and it makes the check-count contrast undeniable.
8. **Revocation** dramatics.

Steps 2–4 alone make a compelling demo. Everything after raises the score.

**The one-line test for whether the UI is doing its job:** can someone who has never seen Wakalah watch a routine payment and then the cloned-agent attempt, and *see* that the system decided to work harder the second time? If yes, the orchestration criterion is won on screen rather than in narration.
