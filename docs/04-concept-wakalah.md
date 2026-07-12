# 04 — Concept Spec: Wakalah (وكالة)

**One-liner:** Wakalah issues signed, expiring **trust tokens** that bind an AI agent to a verified, present, un-hijacked human principal via telecom signals — so banks, merchants, and remittance providers can accept agent-initiated transactions.

**Theme:** 4 — Secure Fintech, Payments & Anti-Fraud Innovation. (Theme 1, Trusted Digital Identity, is the adjacent fit — declare 4, mention 1 once.)

**Name:** *Wakalah* is the classical Islamic-finance **agency contract** — a principal (muwakkil) formally authorizes an agent (wakeel) to act on their behalf. We are digitizing a trust structure this region has operated for fourteen centuries, for the newest kind of agent. This framing is the answer to the "regional relevance" rubric line — it makes a global infrastructure play culturally *ours*, and it will land hard at MWC Doha.

## 1. Problem

It's 2026: AI agents book, buy, and send money on people's behalf. Payment rails are racing to authorize them (Google's AP2 mandates, OpenAI/Stripe's agentic-commerce protocol, Visa/Mastercard agent programs — *verify current names/status before deck-final*). But every one of those schemes authorizes **the agent's credentials**. None of them can answer the question the receiving side actually cares about:

> Is this agent still acting for a real, present, un-hijacked human — right now?

Stolen credentials plus a cloned agent look identical to the real thing at the protocol layer. The only ubiquitous, hard-to-fake anchor tying software to a physical person is the **mobile network**: the SIM in their pocket, its swap history, the device it lives in, its reachability. Operators own that signal — and today it's not wired into agent commerce at all.

**Flagship regional wound:** remittances. GCC corridors are the world's largest (tens of billions of USD yearly from Saudi/UAE/Qatar to Egypt, South Asia, the Levant — *verify figures*). Remittance fraud playbooks start with a SIM swap; agent-mediated remittances will inherit them on day one, at machine speed. Secondary use case (round-2 addition): **travel banking** — Device Roaming Status + Location Verification lets a bank distinguish "customer genuinely abroad" from "fraudster with a swapped SIM," killing false declines for the region's enormous expat/diaspora population.

## 2. The core object: an expiring, revocable trust token

```
WAKALAH TOKEN  (signed JWT)
├─ principal:  hash(MSISDN) + operator attestation ref
├─ agent:      agent ID + public key fingerprint
├─ scope:      "remittance ≤ 2,000 QAR/mo → beneficiary X"
├─ risk:       score + evidence refs (nv ✓, simswap ✓ 190d, device ✓)
├─ issued/expires:  TTL hours-to-days, renewable
└─ revocation: event-driven (see Sentinel)
```

Merchants/PSPs call one **verify endpoint** before honoring an agent-initiated transaction. The differentiator vs. every existing SIM-swap-check product **and** vs. Africa Ignite's winning TrustScore: **continuous revocation** — Wakalah subscribes to SIM-swap events, so a hijack *after* issuance kills the token mid-flight. Not a point-in-time score; a standing, breathing mandate. (If NaC event subscriptions disappoint in the spike, fast polling emulates it — the demo still lands.)

## 3. API orchestration map — the full identity bureau (updated Jul 6 after the catalog, doc 08)

The catalog surfaced six identity APIs the hackathon brief never listed. Wakalah is no longer "SIM-swap plus a token" — it orchestrates the **operator's entire identity stack**, grouped by the trust dimension each signal answers:

| # | NaC API | Trust dimension | Role in the chain |
|---|---|---|---|
| 1 | Number Verification | **Binding** | Mandate creation: cryptographically ties the principal's SIM to the agent authorization (needs 3-legged consent flow — spike item #1) |
| 2 | **KYC Match** | **Identity** | Mandate proofing: claimed name/ID-document matches the SIM's registered owner — the wakeel acts for a *named* muwakkil, not just a number |
| 3 | SIM Swap (check + events) | **Hijack** | Recent swap blocks issuance; swap event **revokes** outstanding tokens mid-flight |
| 4 | Device Swap | **Hijack** | Same SIM, new hardware → step-up re-verification |
| 5 | **Call Forwarding Signal** | **Hijack** | Active unconditional forwarding = OTP/voice interception risk → block voice-verified scopes (vishing precondition nobody else checks) |
| 6 | **Number Recycling** | **Continuity** | "Is this still the same human?" — kills the reassigned-number takeover class before token renewal |
| 7 | **Tenure** | **Continuity** | Account longevity as trust prior: decade-old subscriber ≠ week-old burner SIM — feeds the risk score |
| 8 | Device Reachability Status | **Context** | Liveness: principal dark for days ≠ "present and consenting" for high-value scopes |
| 9 | Device Roaming Status (+ events) | **Context** | Travel mode: "genuinely abroad" kills false declines; roaming-change-country events re-price risk |
| 10 | Location Verification | **Context** | Optional geo-consistency for high-value transactions |
| 11 | *(roadmap)* KYC Fill-in, Age Verification | — | Instant onboarding of unbanked principals; vulnerable-user (Wali) guardian mode |

Every API answers one question — *is the human behind this agent still who, where, and reachable as expected?* — which is precisely "CAMARA APIs as trusted real-time data sources for agent decisions," the mandatory requirement, verbatim. The risk scorer fuses five dimensions; the demo shows at least binding + hijack + continuity live.

## 4. Agent architecture

```
              WAKALAH PLATFORM  (approved-tools agent runtime)
     ┌────────────────┬─────────────────────┬──────────────────┐
     ▼                ▼                     ▼                  │
 MANDATE AGENT    SENTINEL AGENT        RISK SCORER            │
 runs issuance:   watches SIM-swap /    per-transaction        │
 principal        device-swap /         fusion: scope check +  │
 consent + NV     reachability events   fresh signals →        │
 flow → mints     → revokes tokens,     allow / step-up / deny │
 token            notifies principal                           │
     └────────────────┴─────────────────────┴──────────────────┘
                              │
                    NaC CLIENT ABSTRACTION (MCP / SDK)
                              │
                    Nokia Network as Code APIs

 DEMO ECOSYSTEM (also ours, clearly labeled):
   "Rasheed" — legit consumer agent (sends mother's monthly remittance)
   "Rasheed-Clone" — attacker's copy running on stolen credentials
   Mock remittance provider checkout calling the verify endpoint
```

Note the meta-flex for judges: **an AI agent (Sentinel/Risk Scorer) using network APIs to police other AI agents** — agentic AI squared, in a hackathon whose named criterion is "Agentic AI & Multi-API Orchestration."

## 5. Honesty ledger

| Element | Status |
|---|---|
| Number Verification, SIM Swap, Device Swap, Reachability, Location, Roaming calls | **Real calls** against simulated devices/numbers |
| SIM-swap "attack" trigger | Simulator-triggered if supported; else scripted state change, **labeled** |
| Remittance provider, transactions, both consumer agents | Mock ecosystem we build, labeled — the *product* is the trust layer, and its API calls are real |

## 6. Demo scenario (3-minute storyboard, split-screen)

| Time | Beat | On screen | Live NaC calls |
|---|---|---|---|
| 0:00–0:20 | Hook | "Your AI agent wants to send money home. Who vouches for it?" | — |
| 0:20–0:50 | Mandate | Amina in Doha authorizes agent *Rasheed*: monthly 2,000 QAR to her mother. Token minted; payload shown | Number Verification, SIM Swap baseline |
| 0:50–1:25 | Legit flow | Rasheed hits the remittance checkout; provider calls `POST /verify`; all green → transfer approved | SIM Swap, Device Swap, Reachability |
| 1:25–2:20 | The attack | Split screen: fraudster SIM-swaps Amina, launches *Rasheed-Clone* with stolen credentials. Swap event fires → **Sentinel revokes the token mid-checkout** → clone's transaction dies; Amina's phone gets the re-verify challenge | SIM-swap event/poll, revocation, step-up NV |
| 2:20–2:45 | Travel twist (optional if tight: cut) | Amina lands in Istanbul; roaming+location consistency keeps her *own* purchases alive while the stolen-credential path stays dead | Roaming Status, Location Verification |
| 2:45–3:00 | Close | Trust-decision dashboard; "operators become the trust anchor of the agent economy — and bill for every verification" | — |

## 7. Business model & the operator-revenue slide

- **Pricing:** per-verification fee (the exact model banks already pay for SIM-swap checks today — proven willingness to pay) + platform fee for mandate hosting; volume tiers for PSPs/remittance operators.
- **Operator story:** every agent transaction anywhere = 2–5 billable API calls. Operators stop being dumb pipes under the agent economy and become its **identity layer** — this is GSMA's own 2026 thesis, handed back to them as a working prototype.
- **GTM:** remittance operators and PSPs in the GCC first (highest fraud pain, densest corridors); banks' travel-decline problem second; alignment with AP2-style mandate protocols as they standardize.
- **Pivot option on file:** humanitarian aid-distribution verification (same core, NGO buyers) — see doc 01, round-2 notes.

## 8. Honest risks & prepared counters

- **"Local relevance?"** → Wakalah framing + remittance corridors + MWC *Doha* stage. Regional by blood, global by design.
- **"Agentic payments are early."** → The rails are being built *now* (AP2/ACP etc.); fraud infrastructure must precede volume, not chase it. And the judges' own organizations are the ones pushing agentic network APIs.
- **"Isn't this just a SIM-swap check?"** → Those are point-in-time person checks. Wakalah is a *standing mandate* with delegation chain, scope, TTL, and event-driven revocation — the difference between a passport photo and a live guardianship.
- **"Seen TrustScore win Africa."** → Precedent that this archetype wins; our twist (agents as the subject, continuous revocation) is the 2026 sequel, not a rerun.
- **Abstraction in 3 minutes.** → Split-screen human story: a mother's remittance, a thief mid-checkout, a token dying in real time.
