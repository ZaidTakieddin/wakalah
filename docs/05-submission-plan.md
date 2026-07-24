# 05 — Submission Plan: every required artifact, drafted

*Maps 1:1 to the brief's Submission Format. Placeholders in `[brackets]` get filled at the Jul 12 gate (concept) and when the team roster freezes. Where drafts differ per concept, both versions are given — delete the loser after the gate.*

## Artifact 1 — Idea Capture Template (MS Word / PDF)

> ✅ **Superseded (Jul 12–14):** the actual submission document lives at `submission/Wakalah-Idea-Capture.docx` (validated, diagram embedded, all placeholders filled, dated 14 Jul 2026), structured per the organizers' Inspiration Guide. **Jul 14 honesty pass (doc 09 D23):** removed "100% fraud prevention" → "blocks the demonstrated SIM-swap-led takeover"; removed "cryptographic proof the SIM is present" → "network-confirmed possession of the phone number"; performance figures already labeled targets. The deck (not yet built) carries the deeper v2 design — Supervisor + risk-tiered planning + sender-constrained tokens + STEP-UP (doc 04 v2). The drafts below remain deck source material.

> ⚠️ Download the **actual template** from HackerEarth first (doc 02 §1) — field names and dropdowns ("project type", "GSMA pillar") must match theirs, not ours. Below is draft copy per required field from the brief.

| Field | Draft content |
|---|---|
| Idea Name | **MIZAN — Dynamic Thermal Work-Permit & Rescue Agent** · or · **Wakalah — The Trust Layer for AI Agents** |
| Submission Date | [date of upload] |
| Submitter Details | Zaid [surname], team **[team name]**, zaidtakieddin@gmail.com, [phone], [country] |
| Theme | MIZAN → Theme 6 (Climate Resilience & Environmental Monitoring) · Wakalah → Theme 4 (Secure Fintech, Payments & Anti-Fraud) |
| Project Type / GSMA Pillar | Select per template's own options; align to **GSMA Open Gateway** (+ AI). Flag any forced choice we're unsure about in the Discussion tab |
| API Usage | MIZAN: Geofencing subscriptions, Device Reachability Status, Location Retrieval, Location Verification, Number Verification, SIM Swap, Quality on Demand (+optionally Congestion Insights) · Wakalah: Number Verification, SIM Swap (+events), Device Swap, Device Reachability Status, Location Verification, Device Roaming Status |

**Idea Summary — MIZAN (~200 words, tune to template limits):**
> Outdoor workers across the MENA region labor through lethal heat. Qatar law already mandates stop-work above a wet-bulb globe temperature of 32.1 °C, and the UAE, Saudi Arabia and Kuwait enforce summer midday bans — but on real sites, enforcement is a clipboard: static schedules, no view of any worker's accumulated heat exposure, and no rescue workflow when someone goes silent in a danger zone. MIZAN replaces heat *alerts* with a continuously re-evaluated **work permit**: an AI agent layer (risk prediction, shift re-planning, rescue orchestration) governed by a deterministic, statute-encoded safety policy engine. CAMARA network APIs are its ground truth — geofencing and location verify where workers actually are, number-verification and SIM-swap checks prove the device really represents the worker, device reachability turns a dead phone in a red zone into an automatic welfare escalation, and Quality-on-Demand provisions guaranteed connectivity for responders the moment an incident is declared. Because these signals are network-side, MIZAN works on the cheap feature phones site workers actually carry — no app required. Benefits: fewer deaths and heat injuries, automated legal compliance with audit-ready evidence, and minimized productivity loss because the agent re-plans work instead of stopping the site.

**Idea Summary — Wakalah (~200 words):**
> AI agents now book, buy, and send money on people's behalf — but when an agent initiates a transaction, banks and merchants cannot answer the question that matters: is this agent still acting for a real, present, un-hijacked human? Credential-based schemes authorize the *agent*; none verify the *human anchor* behind it. Wakalah — named for the Islamic-finance agency contract — makes mobile operators the trust layer of the agent economy. At mandate creation, CAMARA Number Verification cryptographically ties an agent to its principal's SIM; SIM-swap and device-swap signals block hijacked issuance; and — the key innovation — Wakalah subscribes to SIM-swap events so a hijack *after* issuance revokes outstanding trust tokens mid-transaction, not at the next check. Merchants and remittance providers verify one signed, expiring, scoped token before honoring any agent-initiated payment. Flagship use case: the GCC's remittance corridors — the world's largest — where fraud playbooks begin with a SIM swap; second use case: killing false transaction declines for genuinely traveling customers via device-roaming and location-consistency signals. Benefits: fraud stopped at machine speed, a new per-verification revenue line for operators, and regionally rooted trust infrastructure for the coming wave of agentic commerce.

## Artifact 2 — Pitch Deck (PPT), 12 slides

Required contents from the brief, mapped: problem+context → S2–3 · solution+API usage → S4–5, 7 · AI agent design & orchestration incl. tooling-guide tools → S6 · technical architecture → S7 · business model & monetization → S9–10 · demo screenshots/video links → S8 · team bios & roles → S12.

| # | Slide | Content notes |
|---|---|---|
| 1 | Title | Name, one-liner, team, theme declaration |
| 2 | Problem | Human stakes + the enforcement/verification gap. One number, one image, no bullets-wall |
| 3 | Why now | MIZAN: climate trend + existing statutes + giga-projects/reconstruction · Wakalah: agent-commerce protocols landing 2025–26 + fraud at machine speed |
| 4 | Solution concept | The core object (permit / trust token) — one diagram |
| 5 | Scenario walkthrough | The 3-min demo story in 4 stills |
| 6 | **AI agent design + tools** | Agent roles, decision flow, and the **exact Resource & Tooling Guide tools used** (rubric requires this explicitly). MIZAN adds: "AI proposes, statute-encoded policy disposes" |
| 7 | Architecture & API orchestration map | The APIs-to-decisions table from the concept doc, drawn |
| 8 | Demo screenshots | Real UI incl. the live API-call panel (this is why prototype exists by Aug 10) |
| 9 | Business model | Ours: pricing + GTM. Theirs: **operator revenue per API call** — the GSMA slide |
| 10 | Market & impact | Sized numbers (verify list, doc 06 §5) + socio-economic value |
| 11 | Scalability & roadmap | MIZAN: riders → oil&gas → Hajj/Umrah → Syria reconstruction · Wakalah: remittances → travel banking → AP2-style protocol integration (+aid-distribution option) |
| 12 | Team & ask | Bios, roles, what we'd do with the MWC Doha stage |

Design rules: one idea per slide; the API panel screenshot appears at least twice; every claim on S10 has a source in the appendix; deck exports clean to PDF.

## Artifact 3 — Virtual Demo package

**(a) Screen-recorded video, MAX 3:00.** Storyboards live in the concept docs (03 §7 / 04 §6) — both are timed to 2:40–3:00 with a hard stop. Production notes: script to **2:45**; record UI at 1080p with the **live API-call panel visible during every network call**; one honest sentence labeling synthetic feeds; voiceover over captions (judges skim); export with burned-in timestamps.

**(b) Code repo link.** Checklist before sharing:
- [ ] README: what it is, architecture diagram, quickstart, simulator setup, env vars via `.env.example`
- [ ] `SYNTHETIC_DATA.md` honesty ledger (mirrors concept doc §6)
- [ ] `docs/` includes the tooling-guide compliance note (which approved tools, where in code)
- [ ] Commit history spans the hackathon window (originality evidence) — no bulk "initial commit" dump at the end
- [ ] No secrets in history; license chosen (IP stays ours per rules)

**(c) The four required text blurbs** (drafts; ~70–90 words each — MIZAN version / Wakalah version):

- **Demo description:** M: *"A 3-minute live run of one construction-site scenario: verified worker check-in, AI heat-risk prediction and shift re-planning, an automatic permit revocation on a red-zone geofence event, and a full rescue escalation — unreachable device, last-known location, QoD-provisioned responder video. Every network signal shown is a real CAMARA API call to Nokia Network-as-Code simulators, visible in the on-screen API panel."* · W: *"A 3-minute split-screen: a verified AI agent sends a monthly remittance while its cloned twin — running on stolen credentials after a SIM swap — is revoked mid-checkout by a live network event. Every verification is a real CAMARA call to Nokia NaC simulators, visible on screen."*
- **Commercial value summary:** M: *"Per-worker/month compliance SaaS sold where heat-safety law already compels spend; operators earn per-API-call revenue plus B2B resale margin — a lighthouse case for Open Gateway monetization across construction, delivery, energy, and mass gatherings."* · W: *"Per-verification pricing on rails banks already pay for (SIM-swap checks), extended to every agent-initiated transaction; operators become the paid trust anchor of agentic commerce, starting with the world's largest remittance corridors."*
- **API usage synopsis:** lift rows from the concept doc's orchestration table — one line per API, *decision included*.
- **Business impact statement:** M: *"Fewer heat deaths and injuries, automated statutory compliance with audit-ready evidence, and recovered productivity — sites re-plan instead of stopping. Scales from GCC giga-projects to Hajj heat safety and Syria's reconstruction workforce."* · W: *"Stops agent-economy fraud at machine speed, cuts false declines for traveling customers, and hands MENA operators a new revenue line and strategic position as the identity layer of agentic payments."*

## Phase-2 live-demo runbook (for the shortlist round)

1. **Deterministic scenario engine** — the demo is a scripted timeline driven by the simulation clock; the same inputs produce the same story every run.
2. **Fallback A — replay mode:** every rehearsal records real NaC responses into the replay cache; one env flag serves the demo from cache if the platform/network misbehaves. Disclose only if asked; it *is* real recorded API data.
3. **Fallback B — backup video:** the submitted 3-min video, already open in a tab.
4. **Three timed rehearsals** minimum (doc 06 timeline, Sep 8–13), incl. one on hotel-grade Wi-Fi and one cold-start.
5. Q&A pack: the judge Q&A sections from the concept doc, printed.
