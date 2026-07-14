# HackerEarth submission form copy (paste-ready)

*Prepared 14 July 2026. Attach `Wakalah-Idea-Capture.docx` in the file-upload slot — it IS the required Idea Capture Template (Word). The pitch deck + demo screenshots come via resubmission before Aug 23 (last submission counts).*

## Title

> Wakalah — The Trust Layer for AI-Agent Transactions: operator-verified mandates with continuous revocation, built on Nokia Network-as-Code CAMARA APIs

*(shorter variant if the field is tight: "Wakalah — Telecom-Verified Trust Layer for AI-Agent Payments (CAMARA / Nokia NaC)")*

## Description (rich text)

**Wakalah (وكالة)** — named for the classical Islamic agency contract — is the trust layer for the agent economy: it binds every AI agent to a **verified, present, un-hijacked human principal** using the mobile network's own signals, so banks, PSPs, and remittance providers can safely accept agent-initiated transactions.

**The problem.** AI agents now book, buy, and send money on people's behalf. Every emerging agent-payment scheme authorizes the *agent's credentials* — none can answer the question institutions actually care about: *is this agent still acting for a real, un-hijacked human, right now?* Stolen credentials plus a cloned agent are indistinguishable at the protocol layer. The first victims will be MENA's remittance corridors — the world's largest — where fraud playbooks already begin with a SIM swap and will soon run at machine speed.

**The solution.** Wakalah issues signed, expiring, scoped **trust tokens** at mandate creation, re-verifies the hot signals at every transaction, and — the key innovation — **revokes tokens mid-transaction** the moment the network reports a SIM swap. Three AI agents (Mandate Agent, Sentinel Agent, Risk Scorer) orchestrate the CAMARA APIs as real-time data sources; a deterministic policy engine holds final authority over every verdict (AI proposes, policy disposes).

**CAMARA APIs on Nokia Network-as-Code — ten signals across five trust dimensions:**
- **Binding:** Number Verification (3-legged consent), KYC Match
- **Hijack:** SIM Swap (+events), Device Swap, Call Forwarding Signal
- **Continuity:** Number Recycling, Tenure
- **Context:** Device Reachability, Roaming Status, Location Verification

**AI agent layer (Resource & Tooling Guide compliant):** LangGraph orchestration + Pydantic AI typed decisioning, Gemini 2.5 (reasoning) + Groq Llama (checkout-latency checks) with a local Ollama fallback; Supabase Postgres audit trail; all free tiers.

**Not just an idea — the core chain is already proven live.** 18/18 API operations succeed on the NaC sandbox today, including the complete three-legged Number Verification consent flow (`devicePhoneNumberVerified: true`), QoD sessions, geofencing subscriptions, and the full identity suite — evidence logged in our repo (shared at prototype stage).

**Theme:** 4 — Secure FinTech, Payments & Anti-Fraud Innovation. **Impact:** fraud stopped *before* authorization; false declines cut for genuinely traveling customers; and a new revenue line for operators — every agent transaction generates 2–4 billable verification calls (≈ $40–200 per 1,000 transactions), positioning MENA operators as the paid identity layer of agentic commerce.

**Team Wakalah:** Zaid Takieddin (backend & AI agent layer) · Yasser Al-Koudmany (frontend & demo).

*Full Idea Capture Template attached, including architecture diagram. Working prototype, pitch deck, and demo video to follow in our updated submission.*
