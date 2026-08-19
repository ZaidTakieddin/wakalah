# 03 — Concept Spec: MIZAN (ميزان)

**One-liner:** MIZAN is an AI safety-operations agent that turns GCC heat-safety law into a live, continuously re-evaluated **work-permit system** — when heat conditions turn, it re-plans the shift instead of stopping the site.

**Theme:** 6 — Climate Resilience & Environmental Monitoring (whose suggested API families — Location, QoD, Device Status — are exactly ours). Adjacent to Theme 5 (Industrial & Enterprise AI Automation); we declare 6 and note the adjacency once in the deck.

**Name:** ميزان — "the balance/scale." The policy engine is literally a scale weighing work against life. Keep it.

## 1. Problem

Outdoor labor in the region works through lethal summers. The regulatory response already exists — **Qatar Ministerial Decision No. 17 of 2021 prohibits work when WBGT exceeds 32.1 °C** (plus a Jun 1–Sep 15, 10:00–15:30 outdoor ban); the UAE, Saudi Arabia, and Kuwait enforce summer midday bans with per-worker fines. *(Verify exact current provisions before deck-final — tracked in doc 06 §5.)* But enforcement on real sites is a clipboard: static schedules, thermometer snapshots, no view of any individual worker's accumulated exposure, and no rescue workflow when someone goes silent in a red zone. Companies face a three-way loss: worker deaths and injuries, regulatory fines, and blanket work stoppages that burn schedule because *nuanced* stoppage is administratively impossible.

The ILO projects heat stress will erase ~2.2% of global working hours by 2030 (~80M full-time jobs), with Arab states among the worst affected *(verify figure)*. Giga-projects (NEOM, Qiddiya, urban mega-builds) concentrate hundreds of thousands of outdoor workers; **Syria's reconstruction** is about to add hundreds of thousands more — in 45 °C summers, under contractors with far less safety infrastructure than the Gulf majors.

## 2. The core object: a dynamic work permit

The fundamental object is not a heat alert. It is **a continuously evaluated permission for a task to happen**:

```
PERMIT #8427 — External electrical maintenance, Zone B
duration 45 min · intensity HEAVY · PPE full
worker exposure today: 2h20m · WBGT now 31.8° · predicted +25min: 33.1°
─────────────────────────────────────────────
AI DECISION: ❌ CURRENT PLAN REJECTED
Predicted cumulative exposure exceeds policy (QA MD-17 threshold + budget).
NEW PLAN: start 17:10 · shaded inspection first · Worker B replaces Worker A
          mandatory recovery 25 min
```

Everything else in the product is machinery to keep thousands of these objects correct in real time.

## 3. Upgrades over the original draft (what changed and why)

1. **Identity anchor.** At shift check-in, **Number Verification** proves the device belongs to the registered worker's SIM, and **SIM Swap** confirms the binding wasn't hijacked/rotated. If we treat device presence as *worker* presence in a safety-critical system, that binding must be verified — and it kills "buddy punching" (leaving your phone with a friend). This also extends API usage into NaC's anti-fraud family: all three NaC API families in one product.
2. **Statute-anchored policy engine.** Rules encode the actual Qatar WBGT stop-work threshold and midday-ban windows — MIZAN automates compliance with *existing law*, which converts it from "safety vibes" into a compliance product with a compelled buyer.
3. **Acclimatization budgets.** New workers get reduced exposure limits in week one (standard occupational-heat science — ISO 7243 / ACGIH TLV as design references). Depth like this is what separates us from heat-dashboard teams.
4. **Audit trail as the killer feature.** Every permit decision logs its evidence (WBGT, exposure ledger, API responses) → exportable compliance report. That's the artifact an HSE officer actually buys.
5. **The feature-phone argument.** Network APIs need **no app and no smartphone**: geofencing, reachability, location retrieval, and SIM-swap checks work on the cheap handsets site workers actually carry, keep working when a battery-starved app is killed, and can't be GPS-spoofed. This is the "only a telecom can do this" moment — say it explicitly to judges.
6. **Roadmap absorbs the other ideas.** Same permit engine → delivery riders (platforms under regulatory/PR pressure), oil & gas lone workers, and **mass-gathering heat: Hajj 2024 killed 1,301 pilgrims** *(verify)* — the crowd-safety concept lives on as our expansion slide, not a competing submission. Syria reconstruction is the founder-credibility market entry.
7. **One scenario.** One construction site, four demo stages. No Hajj+city+port buffet.

## 4. API orchestration map (the slide that wins Complexity)

| # | NaC API | Signal | Decision the agent makes with it |
|---|---|---|---|
| 1 | Geofencing subscriptions | zone entry/exit events | Permit validity is zone-scoped: entering a hotter zone re-prices the permit; entering a RED zone revokes it |
| 2 | Device Reachability Status | reachable / unreachable | Welfare-check escalation ladder: silence + heat + red zone = rescue trigger, not a retry loop |
| 3 | Location Retrieval | last known position | Rescue targeting for an unreachable worker — works with no app installed |
| 4 | Location Verification | "is device within zone X?" | Presence proof at permit issuance and stop-work compliance verification |
| 5 | Number Verification | SIM ↔ worker binding | Trust the device as a proxy for the human before any of the above matters |
| 6 | SIM Swap | recent swap? | Invalidate the binding; force re-verification at check-in |
| 7 | Quality on Demand | provisioned session | When Rescue Agent declares an incident, guarantee bandwidth for responder video/telemetry at a congested site |
| 8 | *(optional)* Congestion Insights | site cell congestion | Pre-position comms: schedule heavy telemetry off-peak; early warning that alerts may not deliver |

Rows 1–7 are demoed live against simulators; row 8 only if the spike shows it behaves.

## 5. Agent architecture

```
                     MIZAN ORCHESTRATOR  (approved-tools agent runtime)
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   RISK AGENT          PLANNER AGENT       RESCUE AGENT
   fuses WBGT feed +   re-plans tasks/     runs incident ladder:
   exposure ledgers +  rotations under     check-in → reachability →
   zone states →       policy constraints  location retrieval →
   predicts breaches   (min. productivity  escalate → QoD session
   per zone/worker     loss)               for responders
        │                   │                   │
        └───────────► DETERMINISTIC POLICY ENGINE ◄───────────┘
                      (statute thresholds, exposure budgets,
                       acclimatization rules — hard gates)
                                  │
                            AUDIT LOG → compliance export
                                  │
                     NaC CLIENT ABSTRACTION (MCP / SDK)
                                  │
                        Nokia Network as Code APIs
```

**The defensible line for judges:** *AI predicts and plans; deterministic policy disposes.* No LLM ever holds final authority over a safety decision — it proposes plans that the statute-encoded engine gates. This is much stronger in front of technical judges than "our GPT decides who can work."

**Compliance boundary (tooling guide):** the mandatory-tools restriction binds the **AI agent component** (orchestrator + three agents). The policy engine, solver, FastAPI service, and UI are conventional software. This is our reading of the brief — confirm against the guide, and ask organizers if ambiguous (doc 02 §3).

## 6. Honesty ledger (what's real vs. synthetic in the demo)

| Element | Status |
|---|---|
| All NaC API calls (geofence, reachability, location, verification, SIM-swap, QoD) | **Real calls** against Nokia-sanctioned simulated devices |
| WBGT / weather feed | **Synthetic, clearly labeled** — in production this is site sensors + weather APIs; environmental data is not a network API, so simulating it fakes nothing about our thesis |
| Worker roster, task list | Synthetic demo data |

Repo carries `SYNTHETIC_DATA.md`; the video says it in one honest sentence. Judges reward this — the brief itself encourages simulators.

## 7. Demo scenario (3-minute storyboard)

| Time | Stage | On screen | Live NaC calls in the API panel |
|---|---|---|---|
| 0:00–0:20 | Hook | "At 32.1 °C wet-bulb, work must legally stop in Qatar. Enforcement is a clipboard." One stat, one photo | — |
| 0:20–0:45 | 1 · Normal ops | Control center: 18 workers, 7 permits active, zones green/yellow; check-in shows verified binding | Number Verification, SIM Swap, geofence heartbeat |
| 0:45–1:25 | 2 · Risk develops | Zone B WBGT climbs 29.1→32.4; Risk Agent predicts 91% breach in 25 min; Planner proposes re-plan; supervisor clicks **APPLY SAFE PLAN**; permits re-issued, map re-flows | Location Verification on affected workers |
| 1:25–2:05 | 3 · Violation | A worker's device enters the red zone → permit auto-revoked, exit timer, supervisor ping | Geofence entry event (webhook or poll) |
| 2:05–2:40 | 4 · Emergency | Missed check-in → device **UNREACHABLE** → last location retrieved → Rescue Agent escalates → **QoD session provisioned** for responder video | Reachability, Location Retrieval, QoD create |
| 2:40–3:00 | Close | Audit-trail export; one revenue line ("every decision you saw = billable operator API calls"); roadmap flash (riders / oil&gas / Hajj / Syria) | — |

## 8. Business model & the operator-revenue slide

- **Product pricing:** per-worker/month compliance SaaS (order of $2–5/worker/mo) + site licenses; insurance partnerships (premium discounts for MIZAN-covered sites); ESG/compliance reporting module.
- **Operator story (the slide GSMA is waiting for):** a 1,000-worker site generates tens of thousands of billable API events/day (geofence events, reachability checks, verifications, QoD sessions). MNO B2B arms (stc Business, e& enterprise, Ooredoo Business) resell MIZAN as a VAS — operators earn per-call revenue *and* channel margin. We are a lighthouse case for API monetization.
- **Market:** millions of outdoor workers across GCC construction/logistics/energy *(size precisely before deck-final)*; entry via Qatar (statute exists) and Saudi giga-projects; expansion — delivery platforms, oil & gas, Hajj/Umrah season ops, Syria reconstruction.

## 9. Judge Q&A (prepare, don't improvise)

- **"Why not a GPS app and wearables?"** Site workforces churn across subcontractors and carry cheap/feature phones; there is nothing to install and nothing to charge. Network-side signals survive a dead app and a dead battery (reachability *is* the dead-battery detector). Carrier location can't be GPS-spoofed to fake presence. QoD and slicing exist only network-side. Wearables are a complement we'd integrate, not a substitute.
- **"Privacy? This is worker surveillance."** Consent at employment onboarding, scoped to shift hours and site geofences; zone-level presence, not continuous tracks; CAMARA's operator-side consent framework underneath; retention limits + audit; compliant with Saudi PDPL / Qatar PDPPL / UAE PDPL *(verify names)*. And the data's only function is keeping the worker alive — the audit trail protects workers *from* employers, too.
- **"What if the operator doesn't cover the site?"** Multi-operator via Open Gateway federation is the whole point of CAMARA standardization; MVP targets single-MNO enterprise SIM fleets (common for contractors).
- **"LLM deciding safety?"** No — see §5: deterministic statute gates; agents propose.
