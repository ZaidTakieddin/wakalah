# 04 — Concept Spec: Wakalah (وكالة)

> **v2 (Jul 14)** — hardened after the project review (doc 09 D23). The concept is unchanged; what changed is that the AI's reasoning is now **load-bearing and visible** (risk classification → dynamic verification plan), the token is **sender-constrained**, and every overclaim is stripped. Superseded phrasing from v1 is noted inline where it matters.

**One-liner:** Wakalah issues signed, expiring, **sender-constrained trust tokens** that bind an AI agent to a **network-verified, un-hijacked** human principal via telecom signals — so banks, merchants, and remittance providers can accept agent-initiated transactions.

**Theme:** 4 — Secure Fintech, Payments & Anti-Fraud Innovation. (Theme 1, Trusted Digital Identity, is the adjacent fit — declare 4, mention 1 once.)

**Name:** *Wakalah* is the classical Islamic-finance **agency contract** — a principal (muwakkil) formally authorizes an agent (wakeel) to act on their behalf. We are digitizing a trust structure this region has operated for fourteen centuries, for the newest kind of agent. This is the answer to the "regional relevance" rubric line, and it lands hard at MWC Doha.

**Positioning (review pt 20):** Wakalah is a **trust layer for *other* AI agents** that happens to *contain its own* reasoning agent. It satisfies the mandatory AI-agent requirement without becoming a chatbot or shopping assistant — the agent's job is risk analysis, verification planning, and evidence interpretation, not conversation.

## 1. Problem

It's 2026: AI agents book, buy, and send money on people's behalf. Payment rails are racing to authorize them (Google's AP2 mandates, OpenAI/Stripe's agentic-commerce protocol, Visa/Mastercard agent programs — *verify current names/status before deck-final*). But every one of those schemes authorizes **the agent's credentials**. None can answer the question the receiving side actually cares about:

> Is this agent still acting for a real, un-hijacked human — right now?

Stolen credentials plus a cloned agent look identical at the protocol layer. The only ubiquitous, hard-to-fake anchor tying software to a physical person is the **mobile network**: the SIM, its swap history, the device, its reachability. Operators own that signal — and today it's not wired into agent commerce at all.

**Flagship regional wound:** remittances. GCC corridors are the world's largest (tens of billions USD yearly to Egypt, South Asia, the Levant — *verify figures*). Remittance fraud playbooks start with a SIM swap; agent-mediated remittances inherit them on day one, at machine speed. Secondary: **travel banking** — Roaming + Location lets a bank tell "customer genuinely abroad" from "fraudster with a swapped SIM," killing false declines.

## 2. The core object: a sender-constrained, revocable trust token

The v1 token was a signed, scoped JWT. The review (pts 10–12) hardened it so a **stolen token alone is useless**: the token is **bound to the agent's public key**, and the agent must **prove possession** of the matching private key on every request.

```
WAKALAH TOKEN  (signed JWT, sender-constrained)
├─ principalId          (hashed MSISDN + operator attestation ref)
├─ agentId  +  agentKeyFingerprint     ← token bound to this keypair
├─ action / amountLimit / currency / beneficiaryRestrictions
├─ scope                "remittance ≤ 2,000 QAR/mo → beneficiary X"
├─ riskScore  +  evidenceRefs          (nv ✓, kyc ✓, simSwap 190d, device ✓)
├─ policyVersion  +  tokenId (jti)  +  audience (aud)
└─ issued / expires     (short TTL, renewable)
```

- **Proof of possession (pt 11):** the agent signs each transaction request with its private key; Wakalah verifies against the registered `agentKeyFingerprint`. A replayed token without a fresh valid signature is rejected.
- **Rich mandate (pt 12):** `amountLimit`, `beneficiaryRestrictions`, `audience`, and `jti` stop a valid token from being reused for an *unauthorized* action or at the wrong merchant.
- **Revocation (pt 8–9):** event-driven — see §4 Sentinel. The event is a **machine-to-machine notification from the operator to the Wakalah backend**; Wakalah revokes automatically. The attacker is **never** asked whether to continue.

Merchants/PSPs call one **verify endpoint** before honoring an agent-initiated transaction.

**Standards alignment (D25).** What we call a "sender-constrained token with proof-of-possession" has an industry name: **DPoP** (Demonstrating Proof-of-Possession), part of the **FAPI 2.0** security profile that banks build to. Say it that way to technical judges — it signals we know the production bar:

| Our design element | Standard it maps to |
|---|---|
| Sender-constrained trust token | **DPoP** (public/mobile clients) or **mTLS** (confidential server partners), per **FAPI 2.0** |
| Partner OAuth integration | OAuth 2.0 + **PKCE**, hardened with **PAR** (pushed authorization requests) + **JAR** (signed request objects) |
| Operator consent flow (NV) | 3-legged OAuth authorization-code flow with PKCE, initiated **from the user's device** — **RFC 8252** (external user-agent, never an embedded WebView) |
| STEP-UP human approval | **WebAuthn / passkeys** — phishing-resistant, per **NIST SP 800-63B** AAL2/AAL3 *(production path)* |
| Device binding | Hardware-backed keys + **Play Integrity** / **App Attest**, verified server-side *(production path)* |
| Mobile app hardening | **OWASP MASVS** *(production path)* |

**Scoping note (for a 2-person build):** design the keypair binding into the token model and the deck now (cheap, high-credibility); implement the signature-verify path in the prototype if time allows. The rows marked *production path* are **named, not built** — they require a native mobile app and months of work. Naming them correctly is what earns the credibility; pretending to have built them would lose it.

**Honest gap (state it before a judge finds it):** operator signals prove *possession and account integrity*, not that **the human approved this specific transaction**. Human intent enters our design at two points: the operator consent flow at mandate creation, and STEP-UP re-verification. Device-bound **passkey transaction signing** is the documented production upgrade that closes it fully.

## 3. API orchestration — a core spine + a risk-triggered escalation toolkit

The catalog (doc 08) surfaced six identity APIs the brief never listed. The review (pts 6–7) rightly says a focused MVP beats ten fragile integrations — but our differentiation *is* the depth of orchestration. The synthesis: a **guaranteed 4-API spine** for every mandate, plus a **6-signal escalation toolkit the agent pulls only when risk warrants**. That is *more* agentic than calling ten every time — the agent chooses, and the demo shows it choosing.

**Core spine (MVP — runs on essentially every mandate/verification):**

| # | NaC API | Trust dimension | Role |
|---|---|---|---|
| 1 | Number Verification | **Binding** | Mandate creation: **network-confirmed possession** of the phone number via the 3-legged consent flow (*not* proof the human is present — pt 13). **Production caveat (D25):** operator docs (e.g. Orange) show this flow must be **initiated from the user's device over mobile data** — backend-only NV is unreliable by design. Our sandbox probe succeeded headless because **the sandbox auto-approves**; we say so rather than implying production works that way |
| 2 | KYC Match | **Identity** | Claimed name/ID matches the operator's registered owner — the wakeel acts for a *named* muwakkil |
| 3 | SIM Swap (check + events) | **Hijack** | Recent swap blocks issuance; a swap **event revokes** outstanding tokens |
| 4 | Device Swap | **Hijack** | Same SIM, new hardware → step-up |

**Escalation toolkit (pulled by the verification plan on medium/high risk):**

| NaC API | Trust dimension | Pulled when… |
|---|---|---|
| Call Forwarding Signal | **Hijack** | voice-verified scope or vishing risk — active forwarding = interception (nobody else checks this) |
| Number Recycling | **Continuity** | mandate renewal / dormant principal — reassigned number = takeover class |
| Tenure | **Continuity** | new or thin-history principal — week-old burner ≠ decade-old subscriber |
| Device Reachability | **Context** | high-value scope needs liveness (dark for days ≠ present) |
| Roaming Status (+events) | **Context** | cross-border transaction — "genuinely abroad" vs. swapped SIM |
| Location Verification | **Context** | high-value geo-consistency check |

*Roadmap:* KYC Fill-in (instant unbanked onboarding), Age Verification (vulnerable-user "Wali" guardian mode).

The demo's high-risk path **must visibly pull Call Forwarding + a continuity signal** — that is where the moat is on screen.

## 4. Agent architecture — Supervisor + specialist roles + independent Sentinel

The review (pt 21) folds the flat Mandate/Risk/Sentinel triad under a **Supervisor Agent** for clarity. We keep the specialist roles **named and visible** (the Phase-2 rubric scores *multi-agent* orchestration — a single opaque brain would score worse), and we keep the **Sentinel as an independent asynchronous listener** (there is no in-flight transaction to "supervise" when an operator pushes a swap event).

```
        WAKALAH SUPERVISOR AGENT   (LangGraph; Gemini Flash reason / Flash-Lite fast; Ollama fallback)
        request-time decision flow:
           ┌───────────────┬───────────────┬────────────────────┐
           ▼               ▼               ▼                    ▼
      RISK ANALYST     PLAN BUILDER   EVIDENCE INTERP.     EXPLAINER
      classify         select checks   read signals →      human-readable
      low/med/high     for the tier    ALLOW/STEP-UP/DENY  rationale trace
           └───────────────┴───────────────┴────────────────────┘
                              │  proposal (risk, plan, recommendation)
                              ▼
        DETERMINISTIC POLICY ENGINE   (fixed, versioned rules — FINAL authority)
        · enforces a MINIMUM verification floor per risk tier
        · returns ALLOW / STEP-UP / DENY  ·  same facts+rules ⇒ same result (auditable)
                              │
                    NacClient (REST + record/replay)  →  Nokia Network as Code

   INDEPENDENT — SENTINEL (async):  operator swap/device events  →  revoke mandates AND
   put the principal in CHALLENGE-ONLY MODE until secure re-verification
   (machine-to-machine; attacker never in the loop)

   DEMO ECOSYSTEM (ours, labeled):  Amina + agent "Rasheed" (legit) · "Rasheed-Clone"
   (attacker, stolen creds) · mock remittance checkout calling /verify
```

**The decision flow (review pts 1–5, 16–18):**
1. External agent sends the requested **action + mandate** to Wakalah.
2. **Risk Analyst** classifies **low / medium / high** from amount, beneficiary novelty, transaction type, mandate scope, prior behavior, context.
3. **Plan Builder** proposes a **verification plan** matching the tier (core spine for low; spine + targeted escalation signals for medium/high).
4. NacClient calls the selected CAMARA APIs.
5. **Evidence Interpreter** reads the signals and proposes **ALLOW / STEP-UP / DENY** with a rationale.
6. **Policy engine** checks the proposal against fixed rules **and enforces the per-tier minimum-check floor** — the agent may *escalate above* the floor, never *plan below* it. This closes the "what if the AI under-checks a fraudulent request?" hole: *AI proposes the plan and the verdict; policy guarantees the floor and owns the final decision.*
7. Policy issues the final decision; Wakalah records evidence, reasoning, API results, and the verdict.

**STEP-UP is first-class (pt 18):** mixed signals (e.g. a new device with *no* recent SIM swap) resolve to STEP-UP re-verification, not a binary allow/deny — real fraud systems don't treat every anomaly as certain fraud.

**Challenge-only mode (D25):** a hijack event doesn't merely kill outstanding tokens — it puts the principal's account into a **restricted state where every subsequent action requires step-up** until secure re-verification clears it. This closes the window between "we detected the compromise" and "the next transaction arrives," which is exactly the proportionate, risk-based response fraud-prevention frameworks expect.

**Production roadmap outcome:** a fourth verdict, `review` (manual/human queue for very high amounts), is standard in real payment risk engines. We keep **three** in the demo for clarity and name `review` as the production extension.

**Why this is defensibly agentic:** the agent *reasons about the action* (classify → plan → interpret → explain) instead of executing a fixed sequence; a small routine payment genuinely gets fewer checks than a large transfer to a new beneficiary. Meta-flex intact: **an AI agent using network APIs to police *other* AI agents.**

## 5. Honesty ledger (review pts 8, 14, 15, 19)

The UI **distinguishes on screen**: live result · cached result (replay) · unavailable signal · simulated event. Fallbacks are never presented as real network responses. **Mechanism (D25):** every normalized evidence record carries `source ∈ live | cached | replay | simulated` (doc 07 §3.5), so the labelling is generated from the data itself — it cannot drift out of sync with what actually happened.

| Element | Status |
|---|---|
| NV, KYC Match, SIM/Device Swap, Reachability, Roaming, Location, Call-Forwarding, Recycling, Tenure calls | **Real calls** against NaC simulators |
| SIM-swap **revocation event** | Real operator event **only if the sandbox delivers subscriptions**; otherwise a **clearly-labeled simulated event** + fast-poll of SIM-swap retrieve-date (the timestamp change) drives the same revocation. Verify sandbox subscription delivery in the build |
| Remittance provider, transactions, both consumer agents | Mock ecosystem we build, labeled — the *product* is the trust layer, and its API calls are real |

**Claims discipline:** NV = "network-confirmed phone-number possession + operator-record identity matching," **never** "cryptographic proof the human is present" (pt 13). We say "Wakalah blocks the *demonstrated* SIM-swap-led takeover," **never** "100% fraud prevention" (pt 14). Latency/revocation numbers are **design targets until measured**; report actual prototype results after testing (pt 15).

## 6. Demo scenario (3-minute storyboard, split-screen)

Emphasis (pt 22): agent **reasoning steps**, live **signal cards**, the **different verification plans** per risk, and the **final deterministic decision** — not decorative side-by-side cards.

| Time | Beat | On screen | NaC calls |
|---|---|---|---|
| 0:00–0:20 | Hook | "Your AI agent wants to send money home. Who vouches for it?" | — |
| 0:20–0:55 | Mandate | Amina authorizes agent *Rasheed*: ≤2,000 QAR/mo to her mother. Risk **LOW** → core-spine plan → token minted (payload + key-binding shown) | NV, KYC Match, SIM Swap, Device Swap |
| 0:55–1:25 | Legit flow (ALLOW) | Rasheed hits checkout; `/verify`; low risk, spine green, signature valid → **ALLOW** | SIM Swap, Device Swap |
| 1:25–2:20 | The attack (DENY + revoke) | Fraudster SIM-swaps Amina, launches *Rasheed-Clone*. Unusual context → risk **HIGH** → plan **expands** (Call Forwarding + Tenure/Recycling pulled *on screen*) → dangerous signals → **policy DENY**; swap event → **Sentinel revokes the mandate mid-checkout**; Amina gets secure re-verification | Swap event/poll, Call Forwarding, Tenure/Recycling, revocation |
| 2:20–2:40 | Mixed signal (STEP-UP) | Amina's own new phone, no recent swap → risk **MEDIUM** → **STEP-UP**, not deny | Device Swap, NV step-up |
| 2:40–3:00 | Close | Decision dashboard + audit trail; "operators become the trust anchor of the agent economy — and bill for every verification" | — |

## 7. Business model & the operator-revenue slide

- **Pricing:** per-verification fee (the exact model banks already pay for SIM-swap checks today — proven willingness to pay) + platform fee for mandate hosting; volume tiers for PSPs/remittance operators.
- **Unit economics (directional anchors — Twilio Lookup/Verify class ≈ $0.05/lookup; CAMARA operator pricing is negotiated, not public — verify before deck-final):** signal COGS ≈ $0.01–0.10/call; mandate issuance ≈ 4 spine signals once per mandate; per-transaction verify ≈ 2–4 signals raw, reduced by **per-risk-tier signal-TTL caching** (tenure/recycling cached days; swap minutes; forwarding/reachability real-time only for high-value scopes — this TTL policy lives in the policy engine, and it is the *same* risk-tiering that drives the verification plan). Charge placeholders: **$0.15/verify, $1.00/mandate**, volume tiers → 50–70% gross margin. LLM ≈ $0 on free tiers.
- **Operator revenue (the GSMA slide):** per 1,000 agent-initiated transactions ≈ 2,000–4,000 billable operator API calls ≈ **$40–$200 new operator revenue per 1,000 transactions** — on flows monetized at zero today. *(Estimate; label as such.)*
- **GTM:** GCC remittance operators and PSPs first; banks' travel-decline problem second; align with AP2-style mandate protocols as they standardize.
- **Pivot option on file:** humanitarian aid-distribution verification (same core, NGO buyers) — see doc 01.

## 8. Honest risks & prepared counters

- **"Is Number Verification proof the human is there?"** → No — it's network-confirmed *possession* of the number plus operator identity matching. Strong evidence, not mathematical proof of presence or intent. (This honesty is a credibility *asset* with telecom judges.)
- **"What if the AI misclassifies risk and under-checks?"** → It can't check below the policy engine's **per-tier minimum floor**; the agent may only escalate above it. Policy owns the floor and the final verdict.
- **"Isn't this just a SIM-swap check?"** → Those are point-in-time person checks. Wakalah is a *standing, sender-constrained mandate* with delegation chain, scope, proof-of-possession, and event-driven revocation.
- **"One Supervisor — is it really multi-agent?"** → The supervisor coordinates named specialist roles (Risk Analyst, Plan Builder, Evidence Interpreter, Explainer) plus an independent async Sentinel — LangGraph's supervisor-with-workers *is* a multi-agent pattern.
- **"Does this prove the *human* approved the transaction?"** → No — operator signals prove possession and account integrity. Human intent enters at mandate consent and at STEP-UP; device-bound **passkey transaction signing (WebAuthn)** is the documented production upgrade. *(Answering this honestly beats being caught by it.)*
- **"How do you handle consent and different operators' legal bases?"** → Every signal is normalized into one internal evidence record carrying `purpose`, `legalBasis`, and `consentStatus` (doc 07 §3.5), so provider and market differences never leak into the policy engine — e.g. some markets run fraud checks under legitimate interest, others require explicit runtime consent.
- **"What's your production security path?"** → **FAPI 2.0** profile: OAuth 2.0 + PKCE + **PAR/JAR**, sender-constrained tokens via **DPoP** (mobile) or **mTLS** (server partners); **WebAuthn/passkeys** for human approval; hardware key **attestation** for device binding; **OWASP MASVS** for any mobile client. Named deliberately as the hardening path — the prototype demonstrates the trust logic, not a bank's full security stack.
- **"Agentic payments are early."** → Rails are being built *now*; fraud infrastructure must precede volume. The judges' own organizations are pushing agentic network APIs.
- **"Seen TrustScore win Africa."** → Precedent this archetype wins; our twist (agents as the subject, dynamic planning, continuous revocation) is the 2026 sequel.
- **Abstraction in 3 minutes.** → Split-screen human story: a mother's remittance, a thief mid-checkout, a token dying in real time, and a step-up that isn't a false alarm.
