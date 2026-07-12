# 01 — Idea Scoreboard

*Four ideas were on the table (the brief said three, but KYA and Seismograph were both numbered "2"). Scored against the actual rubric, plus a second-round search for stronger alternatives.*

## Scoring method

Weights mirror the published criteria: Relevance 20% · Impact/Business 20% · Innovation 20% · Complexity & API depth 20% · Demo feasibility on NaC simulators 10% · Differentiation (duplication risk inverted) 10%. Scores are judgment calls, not measurements — the sub-scores exist so we can argue about specifics.

| Idea | Rel | Imp | Inn | Cmx | Demo | Diff | **Total** | Verdict |
|---|---|---|---|---|---|---|---|---|
| **MIZAN** — thermal work-permit + rescue agent | 9.5 | 9.0 | 8.5 | 9.0 | 9.5 | 8.5 | **9.0** | **Primary candidate** (upgraded) |
| **Wakalah** (was KYA) — trust layer for AI agents | 7.0 | 8.5 | 10 | 8.0 | 9.0 | 10 | **8.6** | **Parallel candidate** (fixed) |
| Hajj crowd-safety commander | 10 | 8.0 | 7.5 | 9.0 | 7.5 | 6.0 | **8.25** | **Absorbed** into MIZAN roadmap |
| Network Seismograph | 9.0 | 7.0 | 9.0 | 7.0 | 5.5 | 8.5 | **7.8** | **Killed** |

Sensitivity: if the judging panel skews GSMA-strategy people, Wakalah rises (it *is* their agenda); if it skews regional MNO/impact people, MIZAN and Hajj rise. The Jul 12 gate ([doc 02](02-week1-gate.md)) settles it with evidence rather than taste.

---

## MIZAN — 9.0 — primary candidate

**Recap.** Not a heat-alert app: a *continuously re-evaluated permission for work to happen*. Every outdoor task holds a permit; AI agents re-validate it minute-by-minute against WBGT (current + predicted), the worker's cumulative exposure budget, task intensity, PPE, and network-verified presence — and when conditions turn, the Planner Agent **re-plans the shift instead of stopping the site**. Full spec: [doc 03](03-concept-mizan.md).

**Why it scores.** Bulletproof regional relevance (GCC heat, midday-work bans, giga-project labor); the buyer is **compelled by regulation** (Qatar already mandates stop-work at WBGT 32.1 °C — compliance SaaS, not a vitamin); measurable impact (deaths, fines, downtime); the most controllable demo of all four (the only synthetic input is environmental data, which is legitimately not a network API); and 6–7 APIs each with a decision attached.

**Honest risks.** Heat is the obvious Theme-6 topic → others may build heat dashboards (the permit-engine framing differentiates). Judges will ask "why not a GPS app + wearables?" — the answer is drafted in doc 03 §9 (feature phones, no app install, signals survive dead apps, carrier-grade, QoD is network-side only). Map/schedule UI is the heaviest build of the four.

**Upgrades applied** (vs. the original draft): identity anchor (Number Verification + SIM Swap at check-in — kills buddy-punching, adds the anti-fraud API family); statute-anchored policy engine (Qatar MD 17/2021 + UAE/Saudi/Kuwait bans); acclimatization budgets for first-week workers; audit-trail compliance export as the enterprise killer feature; the feature-phone argument; Hajj heat + delivery riders + oil-and-gas as roadmap verticals; **Syria-reconstruction market hook** (we're Damascus-based — personal credibility + expansion market).

## Wakalah — 8.6 — parallel candidate

**Recap.** The trust layer for the agent economy: signed, expiring **trust tokens** that bind an AI agent to a verified, present, un-hijacked human principal via telecom signals — so banks, merchants, and remittance providers can accept agent-initiated transactions. Renamed from "KYA" to **Wakalah (وكالة)** — the Islamic-finance agency contract in which a principal formally authorizes an agent. Full spec: [doc 04](04-concept-wakalah.md).

**Why it scores.** Highest innovation ceiling and near-zero duplication risk; it is *literally GSMA's 2026 agenda* (operators as the trust anchor of agentic commerce); the Africa edition's winner was a trust broker — archetype precedent; demo is pure software (arguably the easiest build); anti-fraud APIs are the most mature, revenue-proven Open Gateway family.

**Honest risks.** "Relevance to local context" is its weakest rubric line — the Wakalah framing + remittance-corridor anchor (GCC corridors are the world's largest) exist precisely to fix it. "Agentic payments are early" objection (counter: Nokia/GSMA's own agentic push, AP2/ACP-style protocols emerging). Abstraction risk in a 3-minute video (counter: split-screen fraud-catch story). Similarity to Africa's TrustScore must be pre-empted: our differentiator is **continuous revocation from SIM-swap event subscriptions** and agent-delegation chains — not a point-in-time person score.

## Hajj crowd-safety commander — 8.25 — absorbed

**Recap.** Multi-agent crowd-safety command platform (sentinel/guardian/commander agents), congestion-as-crowd-density sensing, QoD lanes for medics.

**Why not standalone.** Pilgrimage is a *named theme* — the single most duplicated idea space in this hackathon; Saudi has heavily invested incumbent systems (Nusuk, SDAIA crowd management), making "who buys this?" awkward; and its killer feature (Congestion Insights as crowd sensor) is the API most likely to be coarse/canned on simulators, putting the wow-moment on synthetic data. The strongest parts survive: **Hajj heat safety (1,301 deaths, 2024) is MIZAN's roadmap slide** — same permit engine, next vertical — and the multi-agent command pattern lives on in MIZAN's architecture.

## Network Seismograph — 7.8 — killed

**Recap.** Read mass device-unreachability clusters as a real-time disaster footprint (Türkiye earthquakes, Derna floods); provision QoD/slices for responders.

**Why killed.** The core signal — thousands of devices going dark in a geographic cluster — cannot be produced on NaC simulators; the heart of the demo would be synthetic with real API calls only on the periphery. Phase 2 scores functionality and stability of the *prototype*; this concept structurally can't show its own thesis. Beautiful idea, wrong venue. (Salvage: "reachability sweep + QoD provisioning" appears inside MIZAN's rescue workflow anyway.)

---

## Round 2 — search for stronger alternatives (requested twice)

Verdict: **no new concept beats the top two.** Three strengtheners were found and folded in, one new contender was scored and parked:

1. **Syria-reconstruction hook (→ MIZAN).** 2026 reconstruction will put enormous outdoor workforces into 45 °C summers; a Damascus-based team pitching worker safety carries personal credibility no Gulf competitor can fake. Market/roadmap slides.
2. **Travel-banking use case (→ Wakalah).** Device Roaming Status + SIM Swap + Location Verification lets a bank distinguish "customer genuinely traveling" from "fraudster with a swapped SIM," killing false declines abroad. Adds an underused API and a second revenue story.
3. **Aid-distribution verification — scored ~8.3, parked.** Telecom-anchored verification of aid recipients before mobile-money disbursement (Syria/Yemen/Sudan; diversion is a real, large problem). Massive impact and relevance; parked because its API surface is the same verification core as Wakalah with thinner orchestration, and NGO/UN buyers are slow — documented here as a **Wakalah pivot option** if judges' feedback favors humanitarian framing.

**Considered and rejected** (one line each): drone corridors with QoD/slicing — derivative of Nokia's own showcases; elderly-care guardian — thin API story vs MIZAN; ports/logistics slice orchestration — abstract demo, no emotional hook; school-transport safety — SafeRide (Africa 2nd place) derivative; standalone travel-banking — folded into Wakalah; delivery-rider heat safety — folded into MIZAN roadmap; e-gov step-up authentication — the canonical Open Gateway demo, zero originality; parametric micro-insurance on network signals — actuarial stretch; exam-integrity verification — thin.

---

## Round 3 — after the API catalog + Tooling Guide (Jul 6)

Two new facts moved the board (sources: [08-nac-api-catalog.md](08-nac-api-catalog.md), `docs/AI Resource & Tooling Guide.pdf`):

1. **NaC exposes a hidden identity goldmine** the brief never listed: KYC Match, KYC Fill-in, Age Verification, Tenure, Number Recycling, Call Forwarding Signal. That upgrades **Wakalah from "SIM-swap with a token" to a full operator-grade identity bureau** — 9–11 load-bearing APIs covering binding, hijack, identity, continuity, and context. Multi-API orchestration depth no other team will match, because they won't even find these endpoints.
2. **The Tooling Guide's suggested focus areas lean fraud/identity/fintech** (fraud & digital identity listed first; no climate/safety category — though hackathon Theme 6 remains canonical and fully legitimate).

**Score update: Wakalah 8.6 → 9.0** (Cmx 8→9.5 on the API goldmine; Rel 7→7.5 on guide-focus alignment). **MIZAN holds 9.0** (gains device-status push events for its rescue ladder; loses nothing — but note the organizer-mindset signal). **The race is now a genuine tie; the Jul 12 gate decides on evidence:**
- If the sandbox **three-legged consent flow works** (NV/KYC family drivable) → Wakalah's core chain is proven and its ceiling is the highest in the field.
- If it doesn't, Wakalah loses the cryptographic-binding story (falls back to SIM/device-swap + recycling + tenure + call-forwarding — still strong) while MIZAN barely notices → MIZAN.
- Persistent tiebreak: which story the team can pitch with fire.

**Fresh candidates enabled by the new APIs, scored honestly and dispatched:**
- **Instant migrant-worker financial onboarding** ("KYC Fill-in in a minute") — ~8.4: real financial-inclusion pain, GSMA-classic; but TrustScore-adjacent (Africa's winner) and structurally a *Wakalah onboarding scenario* → folded into Wakalah's roadmap.
- **"Wali" elder/vulnerable digital guardian** (call-forwarding + SIM-swap + recycling watch; age/parental-control signals) — ~8.2: emotionally powerful, MENA-resonant; weak standalone monetization → folded as a Wakalah consumer mode on the roadmap slide.
- **Telco-signal credit scoring for the unbanked** (tenure + recycling + KYC) — ~7.5: consent/privacy minefield, one-hop agentic story → rejected standalone; noted as Wakalah revenue extension.
- **Anti-vishing call-center copilot** (call-forwarding + NV + reachability before high-risk phone banking) — ~7.8: matches the guide's "support copilots" area; narrow → a Wakalah *mode* on the roadmap.
- **SIM-farm / fake-account detection for platforms** (tenure + recycling + connectivity patterns) — ~7.3: real pain, adversarial demo, privacy-icky → rejected.

**Meta-conclusion of the out-of-the-box pass:** the strongest "new idea" was hiding inside idea #2 all along — not a fraud checker, but **the trust registry of the agent economy, backed by the operator's entire identity stack**. Wakalah's spec (doc 04) is updated accordingly.
