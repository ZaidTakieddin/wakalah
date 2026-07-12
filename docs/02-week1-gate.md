# 02 — Week-1 Spike & the Jul 12 Gate

*Purpose: spend Jul 6–12 killing the two unknowns that actually decide the concept choice — the Tooling Guide and simulator behavior — while doing only work that serves both concepts. On Jul 12, lock one concept and append the decision record at the bottom of this doc.*

## 1. Blocking retrievals (Day 1 — Mon Jul 6)

- [ ] **AI Resource & Tooling Guide**: ⚠️ **status Jul 6 — not found on HackerEarth** (Zaid logged in and saw no guide; the brief's Problem Statement contains the sentence "Here is the AI Resource and Tooling Guide (mandatory tools for the AI agent layer)" which was presumably a hyperlink — re-check whether that exact phrase is clickable / dead). **Action: post this in the hackathon Discussion tab and keep the answer in writing:**
  > *Hi organizers — the Problem Statement requires the AI agent layer to be built "only using the tools listed in the Resource & Tooling Guide", but we can't locate the guide on the hackathon page (the referenced link doesn't appear to be accessible). Could you share the guide or point us to it? We want to confirm our agent stack is compliant before committing to an architecture. Thank you!*
  
  Until answered: build agent core behind our abstraction using mainstream, judge-defensible tooling (given Nokia's 2026 Google Cloud ADK/Gemini partnership, that stack is the most guide-likely bet), document the organizer question + timestamps as good-faith compliance evidence, and swap later if the guide demands it.
- [ ] **Idea Capture Template**: download the actual template (Word/PDF) from HackerEarth — we need its real field names and any dropdowns ("project type", "GSMA pillar") before drafting final copy.
- [ ] Every member: self-register at **networkascode.nokia.io**, obtain API credentials, locate the simulator device numbers and docs.
- [ ] Form/confirm the HackerEarth team registration.
- [ ] **NaC MCP connector check**: in a fresh Claude Code session, confirm "RapidAPI Hub – Network as Code" exposes tools (as of Jul 5 it was connected but exposed nothing — two ToolSearch sweeps found no NaC tools; a restart or connector re-scope is likely needed). Fallback for the spike: NaC Python SDK or raw REST via RapidAPI key.

## 2. API spike matrix (Jul 6–11)

Test each API against **simulated devices**. Fill every cell — "didn't get to it" is a gate input equal to "failed."

| API | Needed by | What to verify | Result |
|---|---|---|---|
| Number Verification | **Both** (MIZAN check-in binding; Wakalah mandate creation) | Does the verification flow work with simulator numbers? What auth flow (OIDC redirect?) — can a backend-only demo drive it? | |
| SIM Swap (check / date) | **Both** | Query works on simulators? Can we *set/trigger* a swap event on a simulated number to demo the catch? | |
| SIM Swap **event subscription** | Wakalah (critical) | Webhook subscription supported? Sink URL requirements? Else: polling interval that still demos well? | |
| Device Reachability Status | **Both** | Read reachable/unreachable; can we toggle a simulator device offline? Latency? | |
| Location Retrieval | **Both** | Last-known location of simulator device; accuracy/age fields | |
| Location Verification | **Both** | Verify device within area; polygon/circle formats; response semantics | |
| QoD session create/delete | **Both** | Create a QoD session on a simulated device; profiles available; session lifetime; visible confirmation we can show in UI | |
| Geofencing subscriptions | MIZAN (critical) | Subscription with webhook sink — needs public URL? (tunnel: cloudflared/ngrok). Entry+exit events on simulated movement? Else polling fallback via Location Retrieval? | |
| Device Swap | Wakalah | Works on simulators? | |
| Device Roaming Status | Wakalah (travel-banking angle) | Readable on simulators? Can roaming state be simulated? | |
| Congestion Insights | Neither critical (Hajj legacy) | 30-min curiosity check only — do not sink time | |

Per-API notes to capture: request/response shapes, rate limits, simulator quirks, whether the call works **through the MCP** as well as the SDK. Keep raw responses — they seed the **replay cache** (live-demo fallback).

### 2.5 Findings so far (Jul 6 — first spike via the NaC MCP from Claude Code)

1. **The MCP fires real, authenticated NaC calls but drops response bodies.** An invalid number returned a proper application-level error (`400 INVALID_ARGUMENT "Invalid phone number"` from the SIM-swap endpoint — proof the full RapidAPI→NaC path and auth work), but every well-formed call across five API families (SIM swap, reachability, location verify, roaming, congestion, number verification) rendered "no output". **Consequence: the MCP cannot serve as the agent's data source in its current form — the backend talks to NaC via REST/SDK (responses first-class); the MCP stays as a smoke-test/authoring aid.** If we want the Nokia-endorsed "agents→MCP→NaC" architecture story, our backend can expose its own thin MCP interface over the NaC client — best of both.
2. **Endpoint paths harvested from the MCP schemas** (saved into `backend/spike/nac_spike.py`): sim-swap & device-swap & number-verification under `/passthrough/camara/v1/...`, reachability & roaming under `/device-status/...`, location retrieval `/location-retrieval/v0/retrieve`, location verification `/location-verification/v1/verify`, geofencing `/geofencing-subscriptions/v0.3/subscriptions`, QoD `/qod/v0/sessions`, congestion `/congestion-insights/v0/query`.
3. **Geofencing (CAMARA v0.3)**: CloudEvents subscription with required HTTP `sink` → the tunnel is confirmed necessary for event delivery; but `config.initialEvent: true` **fires an event immediately if the device is already in the zone** — a deterministic, demo-friendly way to show real event delivery without simulating movement.
4. **Congestion Insights is easier than feared**: plain `POST /query` per device returning historical/predicted congestion (no window = next-15-min prediction) — no subscription machinery needed for reads. MIZAN's optional API row 8 got cheaper.
5. **Number Verification confirmed three-legged**: the endpoint takes an `authorization`/`code` from the CSP flow — it cannot be called standalone. Backend must implement the OIDC dance against the simulator CSP, or we demo identity-anchoring via SIM-swap/device-swap checks and present NV as the documented production flow. This is now *the* open question for Wakalah's core chain (gate criterion 2).
6. **QoD create via MCP has a malformed schema** (body swallowed) — test QoD from the spike script instead.
7. **Bonus APIs exposed beyond the brief's list**: KYC Match, Age Verification, Tenure, Number Recycling, Call Forwarding signal (all Wakalah ammo — call-forwarding is a classic interception-fraud signal), plus slice management + device attach. No commitment, but deck slide 11 can mention the runway.

**→ Next executable step:** `backend/spike/nac_spike.py` (fill `.env` from `.env.example` with the RapidAPI key, `pip install requests`, run; set `SPIKE_MUTATIONS=1` for the QoD + geofencing create/delete pass). Paste `spike-results.json` statuses into the matrix above.

## 3. Tooling Guide — OBTAINED Jul 6 (`docs/AI Resource & Tooling Guide.pdf`) ✔

**Verdict: permissive catalog, not a cage — no blocker for either concept.** Gate criterion 1 is satisfied for both. Key facts:

- **Approved agent frameworks:** CrewAI, **LangGraph**, OpenAI Agents SDK, Microsoft AutoGen, **Pydantic AI**, LlamaIndex, Smolagents; visual: Flowise, Langflow, n8n, Dify, Make; enterprise: Vertex AI Agent Builder, AWS Bedrock Agents, Azure AI Foundry.
- **Approved LLM brains (free tiers):** Google AI Studio **Gemini 2.5 Flash/Pro**, **Groq** (Llama/Mixtral/Qwen), OpenRouter, Cohere, Mistral, Together, HF Inference, Cerebras; local: Ollama, LM Studio, vLLM, llama.cpp.
- ⚠️ **Claude & ChatGPT appear only under "coding assistants"** — not in the LLM/agent-brain list. Compliance-safe reading: use them to *write* the code, but the **agent's runtime brain is Gemini and/or Groq**. (OpenAI *Agents SDK* is listed as a framework; still, Gemini+Groq is the cleanest free path.)
- **Memory:** Chroma / Qdrant / Supabase pgvector / Mem0 all approved.
- **Our chosen compliant stack (slide 6 wording):** *LangGraph orchestration + Pydantic AI agents, Gemini 2.5 (reasoning, Free tier) + Groq Llama (fast reactions, free tier) with **Ollama local models as offline fallback (Free)**, Chroma memory (Free, local), CAMARA APIs via Nokia NaC as agent tools; UI on Vercel Hobby (free); backend FastAPI (open-source).* All from the guide; **$0 rule** (Zaid, Jul 7): every component pinned to a free version, no credit card anywhere — details and fallbacks in [09-master-explanation.md](09-master-explanation.md) §6. (FastAPI/Next.js are conventional software, not the AI-agent component.)
- The guide's **Suggested Focus Areas** lean identity/fintech: fraud & digital identity, financial services, healthcare, mobility/logistics, support copilots, telecom agents. **No climate/safety category** — the 7 hackathon themes remain canonical (Theme 6 exists), but this is a real signal about organizer mental model → feeds the gate (favors Wakalah).
- The guide's own tips *mandate our existing plan*: treat each CAMARA API as an agent-decided tool; cache demo data with recorded fallback; **show the agent's reasoning trace on screen**; one polished agent over five half-built ones. Quote these back in the deck/demo — we're compliant *by their own definition of good*.
- Guide mentions Vonage/Aduna sandboxes as alternates — irrelevant for us; the brief mandates ≥1 API on **Nokia NaC**.

Update to spike priorities: with tooling risk gone, the **single decisive spike item is the three-legged consent flow** (`code`/`authorization`) for the identity family (NV, KYC Match/Fill-in, Age, Tenure, Recycling) on sandbox numbers — it gates Wakalah's core chain and both concepts' identity anchors. See catalog: [08-nac-api-catalog.md](08-nac-api-catalog.md).

## 4. Backend scaffold (parallel, concept-agnostic — Jul 8–12)

Per [doc 07](07-repo-and-backend.md): repo init, FastAPI skeleton, **NaC client abstraction** (SDK/MCP/REST behind one interface + replay-cache recorder), WS event bus, scenario clock stub. None of this depends on the gate outcome.

## 5. The Gate — Sunday Jul 12

Criteria **in order** (earlier criteria override later ones):

1. **Tooling Guide fit.** If the guide's approved tools block or seriously burden one concept's agent design, the other concept wins immediately.
2. **Simulator verdict.** A concept whose *core signal chain* failed the spike loses:
   - Wakalah's core chain: Number Verification → SIM Swap (event or fast poll) → token revocation. If Number Verification is unusable on simulators and SIM Swap can't be triggered/demoed, Wakalah weakens decisively.
   - MIZAN's core chain: Geofencing events (or polling fallback) → Reachability → Location Retrieval → QoD. If geofencing subscriptions are unusable *and* the polling fallback is too coarse to demo, MIZAN weakens decisively.
3. **Tiebreak.** If both survive: default to **MIZAN** (standing recommendation — safest rubric fit) *unless* the team's conviction after a 30-minute structured argument is strongly Wakalah. Storytelling energy matters in Phase 2; don't build the concept nobody wants to pitch.

Also decided at the gate: theme declaration (MIZAN→6, Wakalah→4), product name freeze, and which concept doc gets promoted to "the spec."

## 5.5 Live spike results (Jul 7 — run with Zaid's RapidAPI key, `spike-results.json`)

| API | Result | Body seen |
|---|---|---|
| SIM Swap check / date | **200 ✓** | `{"swapped":true}` / rolling `latestSimChange` (~10 min before each call) |
| Device Swap check | **200 ✓** | `{"swapped":true}` |
| Tenure | **200 ✓** | `{"tenureDateCheck":true,"contractType":"PAYG"}` |
| Number Recycling | **200 ✓** | `{"phoneNumberRecycled":true}` |
| Call Forwarding (uncond.) | **200 ✓** | `{"active":true}` |
| KYC Match | **200 ✓** | `{"nameMatch":"false","birthdateMatch":"false"}` — per-attribute matching live |
| Age Verification | **200 ✓** | `{"ageCheck":"true","verifiedStatus":true,"identityMatchScore":60}` |
| Number Verification (no code) | **401** (expected) | Three-legged only — the single flow left to integrate; KYC Match is the working binding alternative |
| Reachability / Roaming / Connectivity | **200 ✓** | reachable, SMS+DATA; roaming FI; CONNECTED_DATA |
| Location retrieve / verify | **200 ✓** | Device lives in Budapest (47.486, 19.079 — testcsp is Hungarian); ⚠️ verify returned TRUE even vs a Dubai circle |
| Congestion query | **200 ✓** | 5-min slices, Low→High across runs, confidence % |
| Geofencing subscription | **201 create / 204 delete ✓** | Accepts external sink; event delivery test needs the tunnel |
| QoD session | **201 ✓** (after fix) | Device must include `ipv4Address`; sessions self-expire |

**Sandbox behavior notes (demo-relevant):** data is dynamically generated and leans "positive" for this number (always-swapped, always-roaming, verify-TRUE-anywhere; congestion varies per call). Working hypothesis: **different simulator numbers carry different personas** — CONFIRMED Jul 7, see §5.6.

### 5.6 Persona matrix (Jul 7 — official roster from the portal API overview, probed live; `persona-matrix.json`)

| Number | Persona | Evidence |
|---|---|---|
| **+99999991000** | **Compromised principal** | swapped ✓, device-swapped ✓, call-forwarding ✓, recycled ✓, roaming, location-verify **FALSE** |
| **+99999991001** | **Clean principal ("Amina")** | all signals negative, CONNECTED_DATA, location-verify **TRUE** |
| +999999904xx (0400/0404/0422) | HTTP-error simulators | every API returns that status (400/404/422) |
| +999999905xx (0500–0504) | Server-error simulators | every API returns that status (500/502/503/504) |

NAI form: `8D8AC610-566D-4EF0-9C22-186B2A5ED793-<suffix>@testcsp.net`. Demo mapping: Amina=1001 (sails through), compromised persona=1000 (revoked mid-checkout); an 05xx number powers a **graceful-degradation beat** (Sentinel survives a 503 with retry/backoff — the Tooling Guide's own tip made visible). Sandbox constraint on record: personas are fixed per number (no mid-demo state flip on one number) — the storyline stages the takeover across the two personas, labeled in `SYNTHETIC_DATA.md`.

**NV three-legged flow — prerequisites verified Jul 7:** `GET /oauth2/v1/auth/clientcredentials` returns client_id/secret off our RapidAPI key ✓; `GET /.well-known/openid-configuration` → `https://auth.eu.nac.nokia.io/oauth2/v1/authorize` + `/token` ✓. Remaining: the authorization-code redirect (`scope=dpv:FraudPreventionAndDetection number-verification:verify`, `login_hint=<phone>`, `redirect_uri=<our backend>`) then token exchange → Bearer call to `/verify`. Full recipe is in the portal overview (copied to docs/08 §1a). W2 timebox stands, now de-risked.

## 6. Decision record

```
Date: 2026-07-07 (gate closed 5 days early — evidence complete)
Decision: WAKALAH (recommendation by Claude, evidence-based; confirm with teammate — tiebreak
          criterion "pitch with fire" already aligns: Wakalah was Zaid's original pick)
Criterion that decided it: #2 simulator verdict — Wakalah's core chain proven beyond its own
          success condition: 8/9 identity signals work TWO-legged on sandbox (only NV proper
          needs the 3-legged flow, and KYC Match provides a working binding alternative).
          MIZAN's chain also fully proven (geofence 201/204, QoD 201, location/reachability OK)
          — so criterion 3 (strategy + conviction) broke the tie:
          (a) differentiation moat: 6 of Wakalah's APIs aren't in the hackathon brief — no other
              team will find them; MIZAN's APIs are the ones every team will use;
          (b) judge-fit evidence: Africa 1st = trust broker; Tooling Guide focus area #1 = fraud
              & digital identity; MWC Doha audience = the exact buyers of "operator as trust anchor";
          (c) build weight for 2–3 people: pure-software split-screen demo vs map/ops-console;
          (d) team conviction: Zaid's original pick.
Tooling Guide constraints adopted: agent runtime = LangGraph/Pydantic AI + Gemini & Groq brains
          (Claude/ChatGPT only as coding assistants); memory Chroma. Doc 02 §3.
Dissent/concerns worth remembering: MIZAN stays the documented runner-up (docs/03 archived, not
          deleted) — if mid-build feedback shows judges weight regional-impact over innovation,
          its emotional demo was the safer floor. Wakalah must keep the Wakalah/remittance MENA
          framing front-and-center to defend the relevance criterion, and NV's OIDC flow gets a
          hard timebox (1 day in W2; KYC-Match binding is the fallback, not a blocker).
```
