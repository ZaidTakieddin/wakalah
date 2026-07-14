# 06 — Timeline, Roles, Risks

## 1. Master timeline (Jul 6 → Sep 13)

Hard external dates: **Aug 23** Phase-1 deadline · **Aug 28–Sep 13** Prototype Phase · resubmission allowed, last counts.

| Week | Dates | Focus | Exit deliverable |
|---|---|---|---|
| W1 | Jul 6–12 | Tooling Guide + NaC registrations + **API spike** (doc 02) + repo/backend scaffold | **GATE Jul 12** — concept locked, decision record written |
| W2 | Jul 13–19 | Agent core v0 on approved tools; policy/token core v0; scenario engine v0; frontend starts against the WS contract (doc 07) | One agent decision made end-to-end from a real NaC call |
| W3 | Jul 20–26 | Full signal chain on simulators; control-center/dashboard v0; **Idea Capture Template v1** | E2E demo stage 1–2 runnable, ugly |
| W4 | Jul 27–Aug 2 | Demo stages 3–4; **deck v1**; **submit Phase-1 "insurance" version** (template+deck v1) | Insurance submission uploaded ✔ |
| W5 | Aug 3–9 | UI polish + API-call panel; internal demo #1; deck v2 | Prototype demoable start-to-finish |
| W6 | Aug 10–16 | **Screenshots into deck**; template+deck final; stats verified (§5) | Final Phase-1 package ready |
| — | Aug 17–20 | **Submit final Phase-1 by Aug 20** (3-day buffer) | Submitted ✔ |
| — | Aug 21–27 | Hardening, replay cache, video script; rest | Video script locked |
| W7–8 | Aug 28–Sep 7 | Prototype-phase finish; **record video by Sep 8** (target 2:45) | Video + repo cleaned |
| Final | Sep 8–13 | **Final submission by Sep 11** (≥48 h buffer); 3 live-demo rehearsals; Q&A drill | Done + rehearsed |

Standing rule: anything that risks a deadline gets cut from scope, never from buffer. The single scenario is the scope — extra features lose to polish every time.

## 2. Roles (2–3 people)

| Who | Owns | Also |
|---|---|---|
| **Zaid** | `backend/` — FastAPI service, **AI agent layer**, NaC/MCP integration, policy engine, scenario engine | Tooling-guide compliance, API spike, replay cache |
| Teammate (frontend) | `frontend/` — control-center UI, live API-call panel, map/split-screen, **video capture & edit** | Deck design pass |
| Third member (if present) | Product: template + deck copy, stat verification, Discussion-tab liaison, QA of demo runs | Rehearsal timekeeper |

If two people: product duties split — Zaid takes template/stats/compliance copy, frontend takes deck design/video. Pitch delivery for Phase 2: decide by Aug 30, rehearse the same person all three times.

## 3. Risk register

| # | Risk | L×I | Mitigation |
|---|---|---|---|
| 1 | **Tooling Guide missing** — not found on HackerEarth (confirmed Jul 6) | H×**Fatal→M** | Organizer question posted in Discussion tab (draft in doc 02 §1) + answer kept in writing; agent core stays behind swappable abstraction on mainstream judge-defensible tooling (ADK/Gemini most guide-likely given Nokia–Google partnership); good-faith evidence trail = compliance defense |
| 2 | Simulator gaps (Number Verification three-legged flow **confirmed Jul 6**, geofence webhooks need public sink) | M×H | NV: implement OIDC dance vs simulator CSP or demo binding via SIM/device-swap with NV as documented production path; tunnel (cloudflared) for sinks; geofencing `initialEvent:true` gives deterministic event delivery |
| 3 | NaC MCP **fires calls but drops response bodies** (confirmed Jul 6) | Certain×L | Backend uses REST/SDK (spike script ready: `backend/spike/nac_spike.py`); MCP demoted to smoke-testing; optionally expose our own MCP interface inside the backend for the Nokia-pattern story |
| 4 | Theme duplication (heat / pilgrimage / fraud all popular) | H×M | Framing is the moat: permit-engine ≠ heat dashboard; standing mandate ≠ SIM-swap check. Slide 2 draws the contrast explicitly |
| 5 | 3-min video overrun / rejected | M×H | Script to 2:45; hard-stop edit; timestamps burned in |
| 6 | Originality challenge | L×H | Fresh repo, continuous commit history, open-source libs declared in README |
| 7 | Privacy/consent judge attack | M×M | Prepared answers in concept docs §Q&A; consent + data-minimization slide note; PDPL/PDPPL references verified |
| 8 | 2–3-person bandwidth | H×H | ONE scenario; W4 insurance submission caps downside; weekly scope review at Sunday sync |
| 9 | Live-demo failure in Phase 2 | M×H | Deterministic scenario engine + replay cache + backup video; 3 rehearsals |
| 10 | Team roster incomplete / bios missing | M×M | Freeze roster + bios by Aug 10 (deck S12 needs them) |

## 4. Week-1 checklist (copy of doc 02 §1, tick here or there)

- [ ] Tooling Guide downloaded → `docs/`, transcribed into doc 02 §3
- [ ] Idea Capture Template (real file) downloaded → `docs/`
- [ ] All members registered on networkascode.nokia.io; credentials in password manager (never in git)
- [ ] HackerEarth team formed
- [ ] NaC MCP verified in fresh session (else SDK/REST fallback confirmed working)
- [ ] API spike matrix filled (doc 02 §2)
- [ ] Repo scaffolded per doc 07
- [ ] **Jul 12: gate held, decision recorded**

## 5. Stats to verify before deck-final (owner: product role)

Every number below is directionally right but must be re-verified with a 2026 source before it appears on a slide:

- Qatar Ministerial Decision No. 17 of 2021 — WBGT 32.1 °C stop-work threshold; summer outdoor ban Jun 1–Sep 15, 10:00–15:30
- UAE midday break Jun 15–Sep 15 (12:30–15:00) + fine amounts; Saudi and Kuwait ban windows
- Hajj 2024 heat deaths (~1,301, official) and Mina 2015 crush (~2,400) — for MIZAN roadmap slide
- ILO: ~2.2% of global working hours lost to heat stress by 2030 (~80M FTE); Arab-states figure
- GCC remittance outflows + Egypt/South Asia corridor sizes; remittance fraud loss estimates — Wakalah
- Agent-payments landscape names/status (Google AP2, OpenAI/Stripe ACP, Visa/Mastercard agent programs) — Wakalah "why now"
- Open Gateway adoption (operator groups/networks signed, 2026 figures) + Nokia NaC partner count (75+ per MWC26 release)
- Data-protection law names: Saudi PDPL, Qatar PDPPL, UAE PDPL
- Per-call pricing anchors for the unit-economics slide (doc 04 §7): CAMARA operator pricing is negotiated/not public — anchor via aggregator list prices (Twilio Lookup/Verify ≈ $0.05, SIM-swap data add-ons $0.01–0.10 at volume; Vonage/Infobip rate cards) and, if possible, an informal quote from a regional MNO contact; RapidAPI/NaC quota on our plan
