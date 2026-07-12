# 00 — Hackathon Decode: what is actually being judged

*Prepared 2026-07-05 from the official HackerEarth brief + external research. Canonical rules = the HackerEarth page; this doc is our strategic reading of it.*

## 1. What this competition really is

GSMA runs Open Gateway to prove one thesis: **mobile operators can earn new revenue by exposing network capabilities as standardized (CAMARA) APIs.** Every hackathon in the Ignite series exists to produce lighthouse use cases for that thesis. Winning submissions are the ones that make GSMA's own argument for them:

1. A real, regionally resonant problem,
2. where **network signals are load-bearing** (not decoration — something only an operator can provide),
3. orchestrated by an **AI agent that makes decisions** from those signals,
4. with a **business model in which operators earn money** (API calls, resale, revenue share),
5. demonstrated in a stable, cinematic 3-minute demo.

Judge the judges: expect GSMA staff, Nokia (platform sponsor, offering technical support), and regional MNO representatives. Each has a box we can tick deliberately — GSMA wants the monetization story, Nokia wants deep NaC usage, MNOs want something they could actually sell to enterprise/government customers tomorrow.

## 2. Intel from the predecessor (Africa Ignite, 2025–26)

MENA Ignite is a template reuse of the Africa Ignite Hackathon (the "avoid complexity of fake African SIM cards" line in the MENA brief is a leftover). What the same organizers rewarded last time:

| Place | Project | Archetype |
|---|---|---|
| 1st (£3k) | **TrustScore — A Portable Trust Broker** | Identity/anti-fraud **infrastructure** |
| 2nd (£2k) | **SafeRide** | Mobility **safety vertical** |
| 3rd (£1k) | **GridGuard** — AI transformer-theft prevention | AI + physical-infrastructure **protection vertical** |

Readings:
- Both of our finalist archetypes have podium precedent: trust infrastructure (→ Wakalah) and safety verticals (→ MIZAN).
- In Africa, agentic AI was a **bonus** criterion. In MENA it is **mandatory** — so agent design quality is the new differentiator, not a nice-to-have. Most teams will bolt a chatbot onto API calls; a genuinely decision-making multi-agent system will stand out.
- Prize pool grew (5/3/2 vs 3/2/1 £k) — GSMA is investing more in this edition; expect more scrutiny and more teams by the deadline (only 10 registrations as of Jul 5 — early).

## 3. The rubric, decoded

**Phase 1 (Idea Capture Template + Pitch Deck, due Aug 23)** scores Relevance / Impact / Innovation / Complexity & Implementation. Notes:
- "Relevance to regional challenges and **local context**" is an explicit line item → generic-global ideas bleed points here.
- "Effective utilization of Open Gateway/CAMARA APIs" + "AI agent design that intelligently orchestrates CAMARA APIs **using only the approved Resource & Tooling Guide**" → the deck must *show* the orchestration logic and *name the tools*.
- Phase 1 is a **documents contest**. Polish is not vanity; it is scored merit. Screenshots of a working prototype in the deck (explicitly requested) are the strongest possible "demonstrates thoughtful planning and effort" evidence.

**Phase 2 (Live demo, Aug 28 – Sep 13)** adds: functionality & stability, smooth end-to-end UX, "Agentic AI & Multi-API Orchestration" as its own criterion, scalability & commercial viability, and pitch quality. Notes:
- Stability is scored → deterministic scenario engine + replay fallback beat live-fragile heroics.
- "Multi-API orchestration" as a named criterion → we should use several APIs *with reasons*, and make the reasons visible in the UI (live API-call panel).

## 4. Compliance map — every rule → what we do

| Rule (from brief) | Our compliance |
|---|---|
| Use ≥1 CAMARA API available on Nokia NaC | Both concepts use **5–7** NaC APIs, each load-bearing (see concept docs §APIs) |
| Mandatory AI agent layer that orchestrates CAMARA APIs as trusted real-time data sources (not user-triggered actions) | Multi-agent architecture where agents consume network signals to **decide** (permits / trust tokens), documented in deck slide 6 + architecture slide |
| AI agent built **only** with tools in the Resource & Tooling Guide | **Top action item: obtain the guide (login-walled; we don't have it yet).** Until then the agent core sits behind a swappable abstraction. Deck slide 6 lists the exact tools used. |
| Original code; solves a real problem | Fresh repo, all code written within the window; commit history = provenance evidence |
| Developed entirely during Jul 1 – Sep 13 (IST) | Repo created after Jul 1; no imported past projects. Open-source libraries and free services are explicitly allowed |
| Align with exactly one of 7 themes | MIZAN → **Theme 6** (Climate Resilience); Wakalah → **Theme 4** (Secure Fintech & Anti-Fraud). Declared once, consistently, in template + deck |
| Team 1–5 | 2–3 members ✔ |
| 18+, resident of Arab League member states or Türkiye | Confirm each member at registration ✔ |
| Submit via HackerEarth; multiple submissions allowed, **last one counts** | Submit an early "insurance" version (~Aug 2), then improve — never risk the deadline |
| IP belongs to the team | Note for repo license choice (private during contest is fine; share repo link in submission) |
| HackerEarth T&Cs | Accepted at registration |

**Good-to-have items we deliberately hit:** multiple CAMARA APIs ✔; intelligent orchestration across APIs ✔; scalable/secure/production-ready design (architecture doc + consent/privacy section) ✔; 5G-optimized angle (QoD/slicing in both demos; mention 5G-capable device path) ✔.

## 5. Traps and non-obvious insights

1. **The screenshot trap.** The Phase-1 deck requires "demo screenshots or video links" — so the prototype must be *visually demoable by ~Aug 10*, two and a half weeks before the Prototype Phase even opens. Our timeline is built around this.
2. **The tooling-guide tripwire.** An otherwise-winning submission can be disqualified on "agent built with non-approved tools." Nothing in the agent layer gets hard-committed before we read the guide.
3. **Simulators are the sanctioned path.** The brief itself encourages simulator numbers. So: real NaC API calls against simulated devices = fully legitimate; *non-network* inputs (weather/WBGT, rosters, transactions) may be synthetic **if clearly labeled** (`SYNTHETIC_DATA.md` in repo + one honest line in the video).
4. **Resubmission is free insurance.** Last submission counts — submit early, iterate.
5. **The operator-revenue slide is not optional.** Phase-2 explicitly scores commercial viability; the GSMA-shaped version of that slide shows *the operator's* P&L (API calls per site per day × price), not just ours.
6. **Nokia NaC went agentic in March 2026** (MCP server; Google Cloud ADK/Gemini partnership; 75+ operator partners). Agents calling NaC via MCP is the pattern the platform sponsor itself promotes — aligning with it flatters the judges' own roadmap. Confirm against the tooling guide.

## 6. Sources

- [GSMA MENA Ignite event page](https://www.gsma.com/solutions-and-impact/gsma-open-gateway/gsma_events/gsma-mena-ignite-open-gateway-hackathon/) (MWC Doha Nov 8–10 2026 showcase, travel paid)
- [Africa Ignite Hackathon on HackerEarth](https://www.hackerearth.com/challenges/hackathon/africa-ignite-hackathon/) (winners, prior rules)
- [GSMA newsroom — Africa Ignite winners](https://www.gsma.com/newsroom/press-release/first-ever-glomos-africa-winners-announced-alongside-gsma-open-gateway-africa-ignite-hackathon-champions/)
- [Nokia NaC × Google Cloud agentic AI, MWC26](https://www.nokia.com/newsroom/nokia-expands-network-as-code-ecosystem-advances-api-based-agentic-ai-with-google-cloud-mwc26/)
- [Talent Arena 2026 Open Gateway Hackathon recap](https://www.gsma.com/solutions-and-impact/gsma-open-gateway/open-gateway-hackathon-at-talent-arena-showcases-developer-innovation-using-network-apis/) (developers wiring Claude/ChatGPT/Cursor + MCP to CAMARA APIs)
