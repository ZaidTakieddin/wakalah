# HackerEarth submission form copy (paste-ready)

*Updated 13 Sep 2026 for the final submission. Attach `Wakalah-Idea-Capture.docx` in the file-upload slot — it IS the required Idea Capture Template (Word).*

## Title

> Wakalah — The Trust Layer for AI-Agent Transactions: operator-verified mandates with continuous revocation, built on Nokia Network-as-Code CAMARA APIs

*(shorter variant if the field is tight: "Wakalah — Telecom-Verified Trust Layer for AI-Agent Payments (CAMARA / Nokia NaC)")*

## Description (rich text)

**Wakalah (وكالة)** — named for the classical Islamic agency contract — is the trust layer for the agent economy: it binds every AI agent to a **verified, present, un-hijacked human principal** using the mobile network's own signals, so banks, PSPs, and remittance providers can safely accept agent-initiated transactions.

**The problem.** AI agents now book, buy, and send money on people's behalf. Every emerging agent-payment scheme authorizes the *agent's credentials* — none can answer the question institutions actually care about: *is this agent still acting for a real, un-hijacked human, right now?* Stolen credentials plus a cloned agent are indistinguishable at the protocol layer. The first victims will be MENA's remittance corridors — among the world's largest — where fraud playbooks already begin with a SIM swap and will soon run at machine speed.

**The solution.** Wakalah issues scoped, expiring mandates at onboarding, re-verifies the hot signals at every transaction, and — the key innovation — **revokes authorization mid-transaction** the moment the network reports a SIM swap. A LangGraph supervisor classifies risk, plans verification, and proposes a verdict; a deterministic policy engine with per-tier minimum-check floors makes the final ALLOW / STEP-UP / DENY. **AI proposes, policy disposes** — the agent can add friction, never remove it, and every override is shown on screen.

**CAMARA APIs on Nokia Network-as-Code — ten signals across five trust dimensions:**
- **Binding:** Number Verification (3-legged consent flow, implemented end to end)
- **Identity:** KYC Match (+ Fill-in at onboarding)
- **Hijack:** SIM Swap (+ operator events), Device Swap, Call Forwarding Signal
- **Continuity:** Number Recycling, Tenure
- **Context:** Device Reachability, Roaming Status, Location Verification

**AI agent layer (Resource & Tooling Guide compliant):** LangGraph orchestration + Pydantic AI typed proposals, Gemini Flash (reasoning) + Flash-Lite (low-latency tier) with a local Ollama fallback; Supabase Postgres audit trail (hash-pseudonymized, gracefully degrading); all free tiers.

**Not just an idea — a working, hosted system.** Backend hardened to 129 offline tests with strict lint/type gates; a deterministic 7-beat demo (clean approval → step-up → scope refusal → SIM-swap revocation → cloned-agent denial → outage challenge) that lands identically on every run; every stream event schema-validated; every signal honesty-labeled live/cached/replay/unavailable. Live demo, public repo, and run instructions below.

**Theme:** 4 — Secure FinTech, Payments & Anti-Fraud Innovation. **Impact:** fraud stopped *before* authorization; false declines cut for genuinely traveling customers; and a new revenue line for operators — every agent transaction generates billable verification calls, positioning MENA operators as the paid identity layer of agentic commerce.

**Team Wakalah:** Zaid Takieddin (backend, agent layer & demo integration) + Yasser Al-Koudmany (frontend console).

## Links (paste into the matching slots)

- **Live demo:** https://wakalah-balance-demo.vercel.app (scenario page drives the 7-beat story; home page takes manual transfers)
- **Backend API + health:** https://wakalah.onrender.com (try `/health`, interactive docs at `/docs`)
- **Repository:** https://github.com/ZaidTakieddin/wakalah — NOTE: currently private; grant judge access or flip to public before submitting
- **Source code:** same repository above (backend/ + frontend/wakalah-balance-demo/)
- **Presentation (.pdf):** [attach the pitch deck export here]
- **Demo video URL:** [paste after upload]
- **Run instructions:** RUNNING.md in the repo root (local run with zero keys in replay mode, or use the hosted links above — no install needed)
