# 09 — Master Explanation

*The "read this and understand everything" document. Written for someone who has never heard of NaC, CAMARA, or this project. It explains every decision we took from day one, every technical choice, every term, and why Wakalah won. **This file is a living document — every significant step gets appended to the Decision Log (§3) and Changelog (§7).***

---

## 1. What is this project, in plain words?

We are competing in the **MENA Ignite Hackathon** — an online competition (July 1 – September 13, 2026) run by the **GSMA**, the global association of mobile network operators (the companies that run cell networks: stc, e&, Ooredoo, Turkcell, Vodafone…). The GSMA wants to prove that mobile networks can offer more than SIM cards and data plans: they can expose their internal knowledge — *is this SIM real? was it recently swapped? where is this device? is it reachable?* — as **APIs** that software developers can build products on. Prizes: £5,000 / £3,000 / £2,000, plus a showcase at **MWC Doha** (a major telecom industry conference, Nov 8–10, 2026).

The hackathon's two mandatory ingredients:
1. Use at least one **CAMARA network API** through the **Nokia Network as Code** platform (both explained below).
2. Build an **AI agent layer** — software powered by AI models that *decides things on its own* using those network signals, rather than just showing data to a user.

**What we're building: Wakalah (وكالة)** — a trust layer for the coming "agent economy." In 2026, AI agents increasingly book, buy, and send money on people's behalf. When an AI agent shows up at a bank or a remittance service saying "I'm authorized to send $500 for Amina," nobody can currently answer the critical question: *is this agent still acting for a real, present, un-hijacked human?* Wakalah answers it using the one thing fraudsters can't easily fake — the mobile network's own records about Amina's SIM card, phone, and identity. Full product explanation in §5.

---

## 2. Glossary — every term, from zero

### The telecom world

- **MNO / operator / carrier** — a Mobile Network Operator; the company your SIM card belongs to.
- **SIM** — the chip (physical or embedded/eSIM) that ties your phone number to you inside the operator's systems.
- **MSISDN / phone number / E.164** — your phone number in international format (`+9639xxxxxxx`). E.164 is the standard that says "start with +, then country code."
- **SIM swap** — moving a phone number onto a different SIM card. Legitimate when you lose your phone; *the* classic first move in bank fraud when an attacker does it (they then receive your one-time passwords). "SIM-swap check" = asking the operator "was this number moved to a new SIM recently?"
- **Device swap** — same SIM, different handset. Another hijack signal.
- **Call forwarding** — a phone setting that redirects incoming calls to another number. Fraudsters enable it silently to intercept voice verification calls. The network knows whether it's on.
- **Roaming** — your phone connecting through a foreign operator's network when abroad. The home operator knows, including which country.
- **Reachability / connectivity** — whether the network can currently reach the device at all, and how (data / SMS only / not at all — e.g., phone off or out of coverage).
- **Number recycling** — operators reclaim inactive numbers and give them to new customers. The previous owner's bank/WhatsApp accounts may still be tied to that number — a quiet account-takeover risk. The operator knows whether the subscriber behind a number changed.
- **Tenure** — how long the current subscriber has continuously held the number. A ten-year-old subscription is a very different trust signal from a SIM activated last week (a "burner").
- **KYC** — "Know Your Customer": the identity data (name, ID document, address, birthdate) the operator collected when the SIM was registered. In most MENA countries SIM registration against a passport/national ID is required by law, which makes operator KYC unusually reliable here.
- **QoS / QoD** — Quality of Service / **Quality on Demand**: asking the network to guarantee bandwidth/latency for a specific device for a period ("give this responder's video call a protected lane").
- **Network slice** — a bigger version of QoD: a virtual private network carved out of the operator's 5G network with its own guaranteed capacity.
- **Congestion insights** — the network's own measurement/prediction of how busy a cell area is.

### The API ecosystem

- **API (Application Programming Interface)** — a way for one program to ask another program questions or give it commands over the internet. "Calling an API" = sending a structured request and getting a structured answer (usually JSON).
- **GSMA Open Gateway** — the GSMA's initiative (launched 2023) to get all operators worldwide to expose the *same* network APIs, so developers can write code once and run it on any network. This hackathon exists to promote it.
- **CAMARA** — the open-source project (hosted by the Linux Foundation, aligned with GSMA) that writes the *standard definitions* of those APIs — exact request/response formats for "SIM Swap check," "Location Verification," etc. Think of CAMARA as the spec, Open Gateway as the commercial rollout.
- **Nokia Network as Code (NaC)** — Nokia's developer platform that implements CAMARA APIs and offers them to developers with documentation, SDKs, and — crucially for us — **simulators**, so you can build against fake-but-realistic devices without touching a real network. The hackathon mandates using NaC.
- **RapidAPI** — a marketplace/gateway through which NaC's APIs are accessed. You get one **API key** (a secret string) that authenticates every request. Our key lives in a local `.env` file that never enters git.
- **Sandbox / simulators / personas** — NaC's fake network. Nokia provides a roster of fake phone numbers; each behaves in a fixed, documented way (a "persona"). We mapped them by probing (see §3, D14): `+99999991001` acts like a clean, safe user; `+99999991000` acts like a fully compromised one (swapped SIM, forwarded calls, recycled number…); numbers ending 0400–0504 always return that HTTP error code (400, 404, 500…) so you can test how your software copes with failures.
- **Webhook / sink / CloudEvents** — instead of you asking the API repeatedly ("polling"), some APIs *push* a message to a URL you provide (the webhook or "sink") when something happens — e.g., "device entered the zone." CloudEvents is the standard envelope format for those messages. Because the sender must be able to reach your URL from the internet, local development needs a **tunnel** (we plan to use **cloudflared** — a free tool that gives your laptop a temporary public URL).
- **HTTP status codes** — every API answer carries a number: 200/201 = success, 400 = your request was malformed, 401 = not authenticated, 403 = not allowed, 404 = not found, 5xx = server-side failure.

### Authentication terms

- **API key** — a secret identifying *our application* to RapidAPI/NaC. Sufficient for most network-status APIs.
- **OAuth 2.0** — the industry-standard protocol for delegated authorization. Two shapes matter here:
  - **Two-legged** — our app authenticates itself (API key / client credentials) and calls the API directly. No end-user involvement. Most NaC sandbox APIs work this way.
  - **Three-legged** — the *end user* must consent in the middle: the app redirects the user's device to the operator's authorization page, the operator confirms which subscriber it is (on a real network, by recognizing the SIM on the connection), and hands back an **authorization code**; the app exchanges that code (plus its **client_id/client_secret**) for a short-lived **access token** (a "Bearer token") which unlocks the actual API call. Number Verification requires this — by design, because it proves *the device itself* participated.
- **OIDC (OpenID Connect)** — a discovery layer on top of OAuth: a well-known URL (`/.well-known/openid-configuration`) that tells you where the authorize and token endpoints live, so you don't hardcode them.
- **JWT (JSON Web Token)** — a signed, self-contained token format. Our Wakalah trust tokens will be JWTs: anyone can verify the signature, nobody can forge the contents.

### AI terms

- **LLM (Large Language Model)** — the "brain": a model (Gemini, Llama, GPT…) that reads text and produces text/decisions. Accessed through an API with its own key.
- **AI agent** — software where an LLM doesn't just chat: it has **tools** (functions it may call — in our case, the CAMARA APIs), a goal, and autonomy to decide *which* tools to call, *when*, and *what to conclude*. The hackathon's core requirement — and its own guide defines "agentic" as: *"treat each CAMARA API as a tool the agent decides when to call, not a button the user presses."*
- **Multi-agent system / orchestration** — several specialized agents cooperating (one issues mandates, one watches for hijacks, one scores risk), coordinated by an orchestrator.
- **LangGraph** — a Python framework for building agents as *graphs* of steps with state — reliable, resumable flows rather than free-form chat loops. Our orchestration layer.
- **Pydantic AI** — a Python agent framework built on Pydantic (the standard data-validation library). It forces agent inputs/outputs into **typed, validated structures** — an agent can't return vague prose where the system expects `{verdict: allow|step_up|deny}`.
- **Gemini** — Google's LLM family; free API tier via Google AI Studio. Our *reasoning* brain.
- **Groq** — a company serving open-source LLMs (Llama, Qwen…) on custom hardware at extreme speed, with a free tier. Our *fast-reaction* brain (per-transaction checks where latency matters).
- **MCP (Model Context Protocol)** — a standard for plugging tools into AI assistants (like the Claude Code assistant used to build this project). We connected an NaC MCP early on; it could *fire* API calls but a quirk hid the responses, so the product talks to NaC over plain REST instead (see D8).
- **Vector database / Chroma** — storage that lets an agent search past information by *meaning*. Approved for us (Chroma) if the agents need memory; not core yet.
- **RAG (Retrieval-Augmented Generation)** — letting an LLM look things up in a knowledge store before answering. Mentioned for completeness; not core to Wakalah.

### Software terms used in this repo

- **REST** — the ordinary style of web API we use: URLs + HTTP verbs (GET/POST/DELETE) + JSON bodies.
- **FastAPI** — a modern Python web framework; our backend service will be built on it (fast to write, automatic validation, first-class WebSocket support).
- **WebSocket** — a persistent two-way connection between backend and browser, used to stream live events (agent decisions, API calls) into the demo UI without refreshing.
- **`.env` file** — a local text file holding secrets (API keys) as `NAME=value` lines. Read by our scripts at startup; listed in `.gitignore` so it can never be committed. `.env.example` is the safe template with empty values.
- **Spike** — engineering slang for a quick, throwaway experiment to answer a specific question ("does this API work on the sandbox?") before committing to a design. Ours live in `backend/spike/`.
- **Persona probe** — our script (`persona_probe.ps1`) that called every simulator number across 9 APIs to map each number's fixed behavior into `persona-matrix.json`.
- **Replay cache** — recorded real API responses that the demo can serve if the live platform misbehaves mid-presentation. Fallback insurance, honestly labeled.
- **Scenario engine** — the backend module that drives the demo as a scripted, deterministic timeline (same inputs → same story every run) instead of hoping live conditions cooperate.
- **`maxAge`** — a parameter meaning "only accept data no older than this" (e.g., location no staler than 600 seconds).
- **`qosProfile` (e.g., `QOS_E`)** — a named quality tier when creating a QoD session.
- **NAI (networkAccessIdentifier)** — an email-like device identifier (`...-1000@testcsp.net`) — an alternative to a phone number.
- **`x-correlator`** — an optional request ID header for tracing calls through logs.
- **Supabase** — a hosted database platform: managed Postgres + auth + realtime + file storage, with a free tier. Wakalah's persistence layer (mandates, tokens, audit trail), accessed only from the backend using a secret "service key."
- **Migration** — a numbered SQL file that changes the database schema. Applied in order and never edited retroactively, so every environment can rebuild the exact same database.
- **`CLAUDE.md`** — instruction files the AI coding assistant loads automatically: the root one carries project-wide rules; `backend/CLAUDE.md` adds backend-specific rules whenever work touches that folder.
- **Skill (Claude Code)** — a saved workflow the assistant runs on demand (typed as `/name`), defined in `.claude/skills/`. Ours: `/log-decision` (update this file properly) and `/nac-spike` (re-run and record the sandbox spike).
- **Subagent** — a scoped helper AI the assistant can spawn for a task. We deliberately define none — the built-in ones (explore, plan, code review) cover a team this size.
- **ruff / mypy / pytest** — the Python quality trio: linter+formatter, static type checker, and test runner. Configured in `backend/pyproject.toml`; run before every push.

### Product terms we coined

- **Wakalah (وكالة)** — the classical Islamic-finance **agency contract**: a principal (*muwakkil*) formally authorizes an agent (*wakeel*) to act on their behalf. We chose the name because we are digitizing exactly that trust structure for AI agents — and because it roots a global idea in this region's own legal/cultural vocabulary (the hackathon explicitly scores "relevance to local context").
- **Principal** — the human who owns the AI agent (Amina).
- **Mandate** — the recorded authorization: "agent X may do Y up to limit Z for principal P."
- **Trust token** — the signed, expiring JWT that encodes a mandate plus its telecom-verified evidence. Merchants verify it before accepting an agent-initiated transaction.
- **Revocation** — killing a token before it expires — in our design, automatically, the moment the network reports the principal's SIM was swapped.
- **Honesty ledger** — our repo file (`SYNTHETIC_DATA.md`, to be written with the demo) declaring exactly which demo inputs are real API calls and which are simulated, so judges never feel tricked.

---

## 3. The Decision Log — every decision, in order, with reasons

**D1 (Jul 5) — Decode the hackathon before ideating.** We researched what actually wins this competition rather than jumping to build. Findings that shaped everything: this is GSMA's marketing vehicle for Open Gateway, so winners are projects that *prove operators can monetize network APIs*; the judging rubric explicitly scores regional relevance, business model, and multi-API "orchestration"; and the Phase-1 pitch deck requires **demo screenshots** — meaning a working prototype is needed by ~Aug 10, weeks before the official Prototype Phase. We also found the predecessor event (Africa Ignite) and its podium: 1st place was **TrustScore, a "portable trust broker"** — evidence that these judges reward identity/trust infrastructure.

**D2 (Jul 5) — Score all ideas against the rubric, kill weak ones honestly.** Zaid brought four ideas. We scored each on the actual judging criteria (relevance / impact / innovation / complexity / demo feasibility / differentiation). Results: **MIZAN** (a heat-safety work-permit system for outdoor workers) 9.0; **KYA→Wakalah** (agent trust layer) 8.6; **Hajj crowd-safety platform** 8.25 — *absorbed* into MIZAN's roadmap because pilgrimage is a named theme every team will chase, and its killer signal (congestion-as-crowd-sensor) was unprovable on simulators; **Network Seismograph** (reading mass device outages as a disaster map) 7.8 — *killed* because its core signal cannot be honestly demonstrated on a sandbox that has no mass outages.

**D3 (Jul 5) — Don't pick yet: run a one-week evidence gate.** Zaid's instinct favored Wakalah; the scores said MIZAN. Instead of arguing taste, we defined a **gate** (decision deadline Jul 12) with ordered criteria: (1) does the mandatory tooling guide block either concept? (2) do each concept's core API chains actually work on the simulators? (3) tiebreak = which story the team will pitch with fire. We spent the week doing only work that served both concepts.

**D4 (Jul 5) — Repo layout.** Zaid's call: `backend/` (Zaid — service + AI agents + NaC integration), `frontend/` (teammate — demo UI), root `docs/` shared. Matches a 2–3 person team where responsibilities must not overlap.

**D5 (Jul 5) — Documentation as markdown in git, not Word/PPT.** The official submission needs Word/PDF/PPT *files*, but drafting in markdown keeps everything reviewable, diffable, and co-editable for weeks; we generate the polished files near the deadline. Also decided: submit an early "insurance" version (HackerEarth counts only the last submission, so early submission removes deadline risk at zero cost).

**D6 (Jul 5–6) — Treat the mandatory "AI Resource & Tooling Guide" as the #1 compliance risk.** The rules say the AI agent layer may only use tools from a linked guide we initially couldn't access. Response: design the agent core behind a **swappable abstraction** so any stack could be plugged in, and draft a written question to the organizers (paper trail = good-faith defense). When Zaid obtained the PDF (Jul 6), it turned out to be a *permissive catalog*. Our stack choice from it: **LangGraph + Pydantic AI** (frameworks), **Gemini + Groq** (LLM brains — both free-tier), **Chroma** (memory if needed). One subtle catch we honor: **Claude and ChatGPT appear only under "coding assistants"** in that guide — so they may help write the code, but the *running product's* brain must be Gemini/Groq/open models. That's why the product doesn't call Claude's API even though Claude is helping build it.

**D7 (Jul 6) — Why Gemini *and* Groq (two brains, not one).** Different jobs: Gemini 2.5 (strong reasoning, generous free tier) for deliberate work — risk fusion, mandate analysis, explanations; Groq-served open models (extremely low latency, free tier) for per-transaction hot-path checks where a demo can't wait seconds. Both are on the approved list; both need no credit card (a guide requirement for team-wide signup).

**D8 (Jul 6) — MCP for exploration, REST for the product.** We connected the "RapidAPI Hub – Network as Code" MCP so the AI assistant building this project could call NaC directly. Finding: it *fires* real authenticated calls but a bug/limitation hides response bodies (only error responses render). Decision: the backend talks to NaC over **plain REST** (responses are first-class); the MCP remains a smoke-testing aid. Bonus: the MCP's tool *schemas* leaked the exact endpoint paths and parameters for everything — which seeded our API catalog.

**D9 (Jul 6) — Build a complete API catalog before finalizing the idea (docs/08).** Reading every schema revealed **six identity APIs the hackathon brief never mentioned**: KYC Match, KYC Fill-in, Age Verification, Tenure, Number Recycling, Call Forwarding Signal. This mattered strategically: an idea built on APIs *nobody else knows exist* has a differentiation moat. It single-handedly raised Wakalah's score from 8.6 to 9.0 — a dead tie with MIZAN.

**D10 (Jul 5–6) — Three "out-of-the-box" ideation passes, on request.** Fresh candidates generated and honestly dispatched: migrant-worker instant financial onboarding (~8.4 — strong, but structurally a Wakalah scenario → folded into its roadmap); "Wali" elder digital guardian (~8.2 — emotionally powerful, weak standalone monetization → folded); anti-vishing call-center copilot (~7.8 → folded); telco credit scoring (~7.5 — privacy minefield → rejected); SIM-farm detection (~7.3 → rejected); plus earlier rejects (drone corridors, ports, school transport…). Conclusion each time: the strongest "new" idea was an upgrade hiding inside Wakalah itself.

**D11 (Jul 6) — Spike scripts as runnable files, not ad-hoc commands.** `backend/spike/nac_spike.py` (Python, for the future backend environment) and `nac_spike.ps1` (PowerShell — written when we discovered **no Python is installed on the dev machine yet**; PowerShell ships with Windows, so the spike could run immediately). Both scripts read the key from `.env`, call every candidate API, and save raw responses to `spike-results.json` — those recordings also seed the replay cache.

**D12 (Jul 7) — The live spike (the gate's evidence).** Run with Zaid's real RapidAPI key. Results: **8 of 9 identity APIs work two-legged** (SIM swap, device swap, KYC Match, Tenure, Recycling, Call-Forwarding, Age — all returning real data with just a phone number); only Number Verification demands the three-legged consent flow (expected — that's its security model); geofencing subscriptions create/delete cleanly (201/204); QoD sessions create (201) once we discovered the device must include an `ipv4Address` (fixed in both scripts); location retrieval/verification, roaming, connectivity, congestion all live.

**D13 (Jul 7) — GATE CLOSED: Wakalah.** Both concepts' chains passed, so strategy broke the tie, on four grounds: **(a) moat** — six of Wakalah's APIs aren't in the brief; MIZAN's APIs are on every theme card and every team will use them; **(b) judge fit** — Africa's winner was a trust broker, the tooling guide's #1 focus area is "AI for Fraud Detection and Digital Identity," GSMA's 2026 agenda is operators-as-trust-anchor, and the MWC Doha audience is exactly who buys that pitch; **(c) build weight** — a split-screen web demo beats a map/ops-console + optimizer for a 2–3 person team, and the effort saved goes into the agent layer where this year's rubric concentrates points; **(d) conviction** — Wakalah was Zaid's original pick, and the gate's own tiebreak says pitch-fire matters. MIZAN is archived as the documented runner-up (its spec, and its best modes — elder guardian, onboarding, anti-vishing — live on Wakalah's roadmap slide). Decision record: doc 02 §6.

**D14 (Jul 7) — Persona mapping.** Zaid pasted the portal's API overview containing the official simulator roster. We probed all 9 numbers × 9 APIs (`persona_probe.ps1` → `persona-matrix.json`): `+99999991001` = clean persona, `+99999991000` = fully compromised persona, `04xx/05xx` = HTTP-error simulators. This gave the demo its cast: Amina (clean) sails through; the compromised persona gets revoked mid-checkout; an error number powers a scripted **graceful-degradation beat** (the Sentinel agent survives a 503 with retry/backoff — turning a tooling-guide judging tip into a visible demo moment). Constraint recorded honestly: personas are fixed per number, so the "takeover" is staged across two personas and labeled as such.

**D15 (Jul 7) — Number Verification de-risked.** The overview documents the full three-legged recipe; we verified the prerequisites live: client credentials retrievable from our RapidAPI key; OIDC discovery returns working endpoints (`auth.eu.nac.nokia.io`). Remaining work is one integration task (redirect → code → token → verify), timeboxed to one day in Week 2, with **KYC Match as the fallback binding** (it matches a *named human* against operator records two-legged — arguably an even better story).

**D16 (Jul 7) — The $0 rule: pin every tool to a free version.** Zaid's directive: use the free versions as specified in the Tooling Guide. Policy adopted (details in §6): prefer tools the guide labels **Free** outright (LangGraph, Pydantic AI, Gemini via AI Studio, Chroma, Ollama, Excalidraw); where a Freemium tool stays (Groq, Vercel), pin to its free tier — no credit card anywhere — and name a Free-labeled fallback. Two consequences worth noting: OpenAI Agents SDK dropped from consideration (pay-per-token fails the rule), and **Ollama joins the stack as the local fallback brain**, which doubles as live-demo insurance — if venue Wi-Fi or free-tier rate limits fail mid-presentation, the agents keep reasoning on a model running on our own laptop.

**D17 (Jul 7) — Development MCP connectors chosen (needs-driven, not maximal).** We audited what would genuinely smooth the build and added exactly two connectors to a repo-shared `.mcp.json`: **Playwright MCP** (repeatable browser automation — demo UI testing and the deck's required screenshots) and **Context7 MCP** (live library docs, so the assistant writes current LangGraph/Pydantic-AI code instead of stale patterns). Everything else was consciously skipped or deferred: git/GitHub stays on the `gh` CLI, browser-interactive work uses the already-present Claude-in-Chrome (which is also how we'll drive the NV OAuth redirect), and heavyweight connectors (Vercel, Supabase, Figma) wait until their trigger actually fires. Rationale table in §6.1.

**D18 (Jul 7) — Supabase adopted as the persistence layer (Zaid's call; supersedes the earlier local-SQLite lean).** Why it fits: it's on the Tooling Guide's list with a free tier that "covers most hackathon projects" (the $0 rule holds — no card for a free org); Wakalah's core evidence artifact is the **audit trail** (every verification verdict with its signals), which deserves a real queryable Postgres rather than JSON files; a shared cloud database means both teammates develop against the same state; and pgvector is onboard if agent memory ever outgrows local Chroma. Boundaries that keep it safe and simple: **server-side only** — the backend holds the service key in `backend/.env`, all access goes through `app/store/` repository modules, schema changes are append-only SQL migrations, and the frontend never touches Supabase (it speaks only the FastAPI contract). This also fires D17's conditional: the **official Supabase MCP** joins the dev toolbox once the project exists (setup snippet in §6.1 — with the access token referenced as an environment variable, never pasted into the committed `.mcp.json`).

**D19 (Jul 7) — Code quality codified where the tools actually read it; skills added, custom subagents consciously skipped.** The rules now live in three enforceable places rather than in anyone's memory: root **`CLAUDE.md`** (nine golden rules — secrets, $0, guide compliance, agents-propose-policy-disposes, NacClient-only-door, deterministic demo, honesty ledger, master-explanation upkeep, commit hygiene — loaded by the AI assistant in every session), **`backend/CLAUDE.md`** (Python/FastAPI standards: ruff + mypy + pytest gates, six architecture invariants, style and test requirements — loaded whenever work touches `backend/`), and **`backend/pyproject.toml`** (the machine-enforced config for those gates), plus a root `.gitignore` that makes committing secrets structurally hard. Placement rule that answers "root or backend?": *assistant/project config must sit at the repo root because that's the only place Claude Code discovers it (`.mcp.json`, `CLAUDE.md`, `.claude/`) — even when the content is backend-focused; language tooling sits inside the folder it governs.* Two **skills** were added under `.claude/skills/`: `/log-decision` (encodes the standing master-explanation instruction, including the chronological-append lesson from two real mistakes in this file) and `/nac-spike` (run the sandbox spike, diff against recorded findings, update the gate doc). **No custom subagents**: the built-in explore/plan/code-review agents cover a 2–3-person hackathon, and every custom definition is maintenance surface we don't need.

**D20 (Jul 12) — Idea submission package built early, triggered by the organizers' nudge email + Inspiration Guide.** The organizers emailed that our idea submission was pending and shared an official **Inspiration Guide** containing seven fully-worked sample ideas — which doubled as competitive intel: two samples (TrustBridge, a cross-border trust score; PayShield, a checkout fraud agent) are Wakalah's *point-in-time* cousins built on the same three commodity APIs, which both **validates our space** (the organizers themselves expect winners here) and **guarantees clone crowding** (inspiration guides breed lookalikes) — so Wakalah's submission states its differentiation explicitly: standing delegation with event-driven revocation vs. moment-in-time person checks, plus six identity APIs no sample touches. Other intel: every sample declares GSMA Pillar = **"Connectivity for Good"** (that resolves our template question), and the guide's PilgrimGuide sample confirms the earlier call to absorb the Hajj idea (now officially commoditized). The deliverable: `submission/Wakalah-Idea-Capture.docx` — mirroring the guide's exact section structure (Team, Integration Context, Theme Relevance + Project Type/Pillar, Solution Overview, Key Features, APIs & Technology, Innovation Highlights, Impact Metrics, Methodology & Architecture) with an embedded architecture diagram (`submission/wakalah-architecture.png`) — schema-validated, with six highlighted placeholders (team name, teammate names, phone, date, optional diagram link) left for the humans. Built with the now-installed Python 3.14 + Node 23 toolchain; submitting early is costless insurance since HackerEarth counts only the last submission.

**D21 (Jul 12) — Submission finalized; repository went live.** Placeholders filled: team **"Wakalah"**, members **Zaid Takieddin** (backend & AI agent layer) and **Yasser Al-Koudmany** (frontend & demo), contact phone added; only the submission date remains as `[DD]` until upload day. The git repository was initialized and the **originality-evidence rule is now active**: first commit `d28ce45` (29 files) pushed to a **private** GitHub repo — <https://github.com/ZaidTakieddin/wakalah> — private on purpose, because the Inspiration Guide guarantees lookalike submissions and our differentiation shouldn't be browsable mid-contest (the repo link goes to judges at final submission). The `.gitignore` was verified before committing: the RapidAPI key (`backend/spike/.env`) never entered history. Collaborator invite for Yasser: his email matches no public GitHub account, and modifying repository access permissions is an action the AI assistant doesn't perform itself — Zaid sends the one-click email invite from the repo's access settings.

---

## 4. Why Wakalah — the short, honest version

Because every form of evidence we could gather pointed the same way:

| Evidence type | What it said |
|---|---|
| Judging rubric | Mandatory agentic AI + multi-API orchestration = Wakalah's whole substance |
| Precedent | The same organizers' previous edition crowned a trust broker |
| Organizer signals | Tooling guide's #1 suggested focus area: fraud & digital identity |
| Live technical spike | Wakalah's chain works on the sandbox *beyond its success condition* |
| Differentiation | 6 of its APIs are effectively secret — no other team will orchestrate them |
| Team reality | Lightest build for 2–3 people; pure software demo |
| Conviction | It was Zaid's own pick — the pitch will have fire |

What we gave up: MIZAN's visceral "worker rescued from heat" story and its regulation-compelled buyer. That's real. The mitigations: Wakalah's demo has its own visceral moment (a thief's cloned agent dying mid-checkout), and the MENA framing (the wakalah contract + remittance corridors) defends the regional-relevance criterion MIZAN would have maxed.

## 5. What Wakalah actually is and what it utilizes

**The problem.** Payment rails are racing to authorize AI agents (Google's AP2 mandates, OpenAI/Stripe's agentic commerce protocol, Visa/Mastercard agent programs). All of them authorize *the agent's credentials*. None can tell whether **the human behind the agent** is still who, where, and as-safe as expected — stolen credentials plus a cloned agent look identical at the protocol layer. The only ubiquitous, hard-to-fake anchor tying software to a physical person is the mobile network.

**The solution.** Wakalah sits between AI agents and the businesses they transact with:

1. **Mandate creation** — Amina authorizes her agent ("send up to 2,000 QAR/month to my mother"). The **Mandate Agent** verifies the binding: Number Verification (the cryptographic proof her SIM is present — three-legged), KYC Match (her claimed name/ID matches the SIM's registered owner), SIM-swap/device-swap recency (not hijacked *right now*), Tenure and Number Recycling (this number has been *her* number, continuously). Out comes a signed, expiring **trust token** (a JWT carrying the mandate scope, a risk score, and evidence references).
2. **Transaction time** — the remittance provider calls Wakalah's `verify` endpoint before honoring the agent. The **Risk Scorer** re-checks the hot signals (swap? forwarding? reachability? roaming/location consistency?) and returns *allow / step-up / deny* with reasons.
3. **Continuous revocation** — the **Sentinel Agent** watches for SIM-swap events; the moment Amina's number is hijacked, every outstanding token dies — *mid-checkout if necessary*. This is the differentiator over every existing point-in-time fraud check (and over Africa's TrustScore).

**The API roster it utilizes** (each answering one plain-English question):

| API | The question it answers |
|---|---|
| Number Verification | "Is the SIM physically present with this request?" (binding) |
| KYC Match | "Does the claimed identity match the operator's registered owner?" (identity) |
| SIM Swap check/date | "Was this number moved to a new SIM recently?" (hijack) |
| Device Swap | "Same SIM, suspicious new phone?" (hijack) |
| Call Forwarding Signal | "Are her calls being silently intercepted?" (hijack — almost nobody checks this) |
| Number Recycling | "Is this still the same human, or was the number reassigned?" (continuity) |
| Tenure | "How long has this subscriber existed?" (trust prior) |
| Device Reachability | "Is her phone alive and reachable right now?" (context/liveness) |
| Roaming Status | "Is she genuinely traveling?" (context — kills false declines abroad) |
| Location Verification | "Is the device where the transaction claims?" (context, high-value only) |
| *(roadmap)* KYC Fill-in, Age Verification | Instant onboarding of unbanked principals; guardian modes for vulnerable users |

**The flagship scenario** — agent-mediated **remittances**: the GCC hosts the world's largest remittance corridors, remittance fraud playbooks begin with a SIM swap, and MWC *Doha* is the perfect stage for it.

**The business model** — per-verification fees (banks already pay exactly this way for SIM-swap checks today — proven willingness to pay), and for the operators: every agent transaction anywhere becomes 2–5 billable API calls. The pitch to the GSMA jury in one line: *operators stop being dumb pipes under the agent economy and become its paid identity layer.*

## 6. Third-party tools — what, why, and the $0 rule

**The $0 rule (Zaid's directive, Jul 7):** nothing in this project may require payment or a credit card. Wherever the Tooling Guide labels a tool **Free**, we use that tool outright; where we keep a **Freemium** tool, we pin ourselves to its free tier and name a Free-labeled fallback. This is also exactly the guide's own promise ("*Every tool listed below has a Free plan or a Freemium tier that is sufficient to build, demo, and submit… no credit card or paid commitment required*") and its team tip ("*pick free tiers that don't require a credit card so the whole team can sign up quickly*").

| Tool | Guide tier | What we use | Why |
|---|---|---|---|
| **Nokia NaC (via RapidAPI)** | Freemium — "free developer portal" | Free developer access + simulators only | Mandated platform; simulators are the sanctioned demo path |
| **LangGraph** | **Free** | Open-source library | Orchestration as auditable graphs — a trust product can't run on a freeform chat loop |
| **Pydantic AI** | **Free** | Open-source library | Typed, validated agent outputs (`allow/step_up/deny`) — what a risk engine needs |
| **CrewAI** | **Free** | Optional, only if role-based sub-agents help | Approved spare part; LangGraph is primary |
| **Gemini (Google AI Studio)** | **Free** — "free API key… very generous request limits" | Free API key | Primary *reasoning* brain (risk fusion, mandate analysis) |
| **Groq** | Freemium — "free API tier with high rate limits" | **Free tier only, no card** | Fast hot-path brain (per-transaction checks). Fallback if limits bite → Ollama ↓ |
| **Ollama** | **Free** | Local Llama/Qwen on our own laptop | The Free-labeled brain fallback — and demo insurance: if venue Wi-Fi or rate limits die mid-presentation, the agent brain keeps running locally |
| **Chroma** | **Free** | Local, `pip install` | Agent memory if needed; zero cloud dependency |
| **Supabase** | Freemium — "free tier covers most hackathon projects" | **Free tier, no card**; service key server-side only | Adopted Jul 7 (D18): Postgres persistence for mandates, tokens, and the audit trail; realtime + pgvector available if ever needed |
| **FastAPI** | *(not in guide — conventional software, outside the agent-component restriction)* | Open-source (MIT), free | Backend service; Python is where all approved agent frameworks live; native WebSockets for the live demo feed |
| **Vercel (frontend hosting)** | Freemium — "generous Hobby tier" | **Hobby (free) tier only**; live demo runs locally anyway | Shareable demo link for the submission. Free-labeled alternative if ever needed: Streamlit Community Cloud (**Free**) |
| **cloudflared** | *(not in guide — infrastructure, free)* | Free tunnel | NaC webhooks need a public URL during development |
| **Excalidraw (+AI)** | **Free** | Architecture diagrams for deck/repo | Free-labeled option in the guide's productivity section |
| **Canva** | Freemium — free plan | Free plan for deck design | Guide-listed; PPT export for the required deliverable |
| **PowerShell (spike scripts)** | *(built into Windows)* | — | Ran the spike with zero installs while Python wasn't set up |
| **Claude Code / Copilot-class assistants** | Freemium (guide: "coding and AI pair-programming") | As **coding assistants only** | The product's runtime brains are Gemini/Groq/Ollama — never Claude/ChatGPT (guide compliance) |

Why not: **OpenAI Agents SDK** (approved, but pay-per-token — fails the $0 rule where Gemini/Groq/Ollama don't); **n8n/Flowise visual builders** (approved and free, but code-first gives the typed policy layer and audit trail judges will probe); **AWS Bedrock / Azure AI Foundry / Vertex Agent Builder** (approved, but credit-based trials that can require cards and expire — needless risk); **Pinecone/Qdrant Cloud** (free tiers exist, but Chroma is Free-labeled and fully local); **Deepgram/ElevenLabs voice** (not needed; if voice ever enters the roadmap demo, the Free-labeled path is self-hosted **OpenAI Whisper**).

### 6.1 Development-time MCP connectors (tools for the AI *coding assistant*, not the product)

Distinct from everything above: **MCP connectors** plug extra abilities into the Claude Code assistant that helps us *build* — they never ship in Wakalah itself (the product's agents call NaC over REST; the guide-compliance question doesn't apply to developer tooling). Configured in `.mcp.json` at the repo root, which git shares with the whole team; Claude Code asks each member to approve them once. All free.

| Connector | What it gives the assistant | Why this project needs it |
|---|---|---|
| **Playwright MCP** (`npx @playwright/mcp@latest`) | Drives a real browser programmatically — click, fill, navigate, screenshot, repeatably | Scripted end-to-end runs of the split-screen demo UI; **captures the demo screenshots the Phase-1 deck requires**; regression-checks the demo before every rehearsal |
| **Context7 MCP** (`https://mcp.context7.com/mcp`) | Fetches current, version-accurate documentation for libraries | LangGraph / Pydantic AI / FastAPI evolve faster than any AI model's training data — this prevents plausible-but-outdated framework code |
| *(already connected)* **NaC MCP** | Fires real NaC API calls from chat | Smoke tests only — its known quirk hides response bodies (Decision D8), so the product and serious testing use REST |
| *(built into the environment)* **Claude in Chrome** | Controls the developer's actual Chrome browser | The Number Verification three-legged flow is a *browser redirect chain* — this is how we drive and debug it interactively (D15) |
| *(built into the environment)* **Claude Code preview tools** | Starts/inspects dev servers with console + network logs | Day-to-day FastAPI/Next.js debugging without leaving the assistant |

**Deliberately not installed:** GitHub MCP (the `gh` CLI through the normal terminal does everything a 2–3-person repo needs); filesystem/memory/fetch MCPs (Claude Code has all three built in); Slack/Jira/Linear (a 3-person team with `docs/06` doesn't need ceremony); Sentry (error tracking is overkill for a hackathon). Conditional adds, only if their trigger fires: **Vercel MCP** (when the frontend actually deploys, ~Aug), **Figma MCP** (only if the teammate designs in Figma first).

**Supabase MCP — trigger fired (D18).** Once the Supabase project exists, add to `.mcp.json` (committed) with the token referenced from the environment — **never paste the actual token into a committed file**:

```json
"supabase": {
  "command": "npx",
  "args": ["-y", "@supabase/mcp-server-supabase@latest", "--read-only", "--project-ref", "<your-project-ref>"],
  "env": { "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}" }
}
```

Each developer sets `SUPABASE_ACCESS_TOKEN` (a personal access token from the Supabase dashboard) in their own shell environment. Keep `--read-only` — the assistant inspecting schema/data doesn't need write access; migrations go through the repo like all other code.

## 7. Changelog

- **2026-07-05** — Hackathon decoded; four ideas scored; Seismograph killed, Hajj absorbed; two-track gate defined (D1–D5). Doc suite 00–07 created.
- **2026-07-06** — Tooling Guide obtained and digested (D6–D7); NaC MCP connected, response-body quirk found (D8); full API catalog built, hidden identity APIs discovered (D9); ideation rounds 2–3 (D10); spike scripts written (D11). Docs 08 + updates.
- **2026-07-07** — Live spike passed across all families (D12); QoD `ipv4Address` fix; **gate closed: Wakalah selected** (D13); official simulator roster probed → persona matrix (D14); NV three-legged prerequisites verified live (D15). This master-explanation file created. **$0 rule adopted** — all tools pinned to free versions per the Tooling Guide, Ollama added as local fallback brain, OpenAI Agents SDK dropped (D16). **Dev MCP connectors set up** — `.mcp.json` with Playwright + Context7; NaC MCP, Claude-in-Chrome, and preview tools noted as already available; GitHub/Vercel/Supabase/Figma consciously skipped or deferred (D17). **Supabase adopted** for persistence — server-side only, repositories + migrations, official MCP queued read-only (D18). **Quality rules codified** — root & backend `CLAUDE.md`, `pyproject.toml` (ruff/mypy/pytest), `.gitignore`, `/log-decision` + `/nac-spike` skills, no custom subagents (D19).
- **2026-07-12** — Organizer nudge email + official Inspiration Guide analyzed (TrustBridge/PayShield samples = Wakalah's point-in-time cousins → differentiation made explicit; GSMA pillar confirmed "Connectivity for Good"); **idea submission package built and validated**: `submission/Wakalah-Idea-Capture.docx` + embedded architecture diagram (D20). **Placeholders filled** (team Wakalah; Zaid Takieddin + Yasser Al-Koudmany; only `[DD]` date remains); **repo live**: private GitHub `ZaidTakieddin/wakalah`, first commit `d28ce45`, no secrets in history; Yasser's collaborator invite handed to Zaid (D21).

*(Every future step appends here: what was done, what was decided, and why — same standard as above.)*
