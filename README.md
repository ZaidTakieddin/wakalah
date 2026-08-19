# MENA Ignite Hackathon — Team Workspace

> **Status (2026-07-12):** WAKALAH selected (gate closed Jul 7; spike fully green). **Idea submission package ready**: [submission/Wakalah-Idea-Capture.docx](submission/Wakalah-Idea-Capture.docx) — fill the 6 highlighted placeholders (team name, members, phone, date) and upload to HackerEarth; resubmission stays open until Aug 23. Inspiration-guide intel folded in ([doc 09 D20](docs/09-master-explanation.md)). **Parallel track: Week-2 build** — backend scaffold per [doc 07](docs/07-repo-and-backend.md), agent core (LangGraph + Gemini/Groq), NV redirect flow (recipe in [doc 08 §1a](docs/08-nac-api-catalog.md)), demo scenario on the mapped personas ([doc 02 §5.6](docs/02-week1-gate.md)). Python 3.14 + Node 23 installed. **Repo:** [github.com/ZaidTakieddin/wakalah](https://github.com/ZaidTakieddin/wakalah) (private) — commit small and often; the history is our originality evidence.

## Key dates

| Date | What |
|---|---|
| Jul 1 – Aug 23, 2026 | Idea Phase (submit Idea Capture Template + Pitch Deck **with demo screenshots**) |
| **Jul 12** | Our internal gate: lock MIZAN vs Wakalah |
| **Aug 10** | Our target: prototype demoable enough for deck screenshots |
| **Aug 20** | Our target: Phase-1 submission (3-day buffer before Aug 23 deadline) |
| Aug 28 – Sep 13 | Prototype Phase (3-min video + repo + live demo round for shortlisted teams) |
| **Sep 8** | Our target: video recorded |
| **Sep 11** | Our target: final submission (≥48 h buffer) |
| Nov 8–10, 2026 | MWC Doha — top-3 showcase (travel paid) |

## Repo layout

```
backend/     — Zaid: FastAPI service, AI agent layer, NaC integration, Supabase storage
frontend/    — teammate: split-screen demo UI + live API-call panel, video capture
docs/        — shared: strategy, specs, submission drafts (this suite)
CLAUDE.md, .claude/, .mcp.json, .gitignore — project rules, skills, MCP connectors
README.md    — you are here
```

## Doc index

| Doc | What it answers |
|---|---|
| [00-hackathon-decode.md](docs/00-hackathon-decode.md) | What is actually being judged + full rule-compliance map |
| [01-idea-scoreboard.md](docs/01-idea-scoreboard.md) | All ideas scored honestly; what was killed, absorbed, upgraded |
| [02-week1-gate.md](docs/02-week1-gate.md) | This week's API spike + how we decide MIZAN vs Wakalah on Jul 12 |
| [03-concept-mizan.md](docs/03-concept-mizan.md) | Full MIZAN spec (permit engine, APIs, agents, demo, business) |
| [04-concept-wakalah.md](docs/04-concept-wakalah.md) | Full Wakalah spec (trust tokens, APIs, agents, demo, business) |
| [05-submission-plan.md](docs/05-submission-plan.md) | Every required submission artifact, drafted |
| [06-timeline-and-risks.md](docs/06-timeline-and-risks.md) | Week-by-week plan, roles, risk register |
| [07-repo-and-backend.md](docs/07-repo-and-backend.md) | Repo conventions, backend blueprint, frontend contract |
| [08-nac-api-catalog.md](docs/08-nac-api-catalog.md) | Full NaC API inventory: endpoints, requests, expected responses, agent-decision notes |
| [09-master-explanation.md](docs/09-master-explanation.md) | **Start here if you're new** — every term explained from zero, every decision with its why, the full Wakalah rationale. Living doc, updated with every step |
| [10-frontend-guide.md](docs/10-frontend-guide.md) | **For the frontend** — how to run it, every API endpoint and live event, TypeScript types, and how the data should be presented on screen |

## Do this week (blocking items first)

1. ✅ **Tooling Guide obtained Jul 6** (`docs/AI Resource & Tooling Guide.pdf`) — permissive; no blocker for either concept. Compliant stack chosen (LangGraph/Pydantic AI + **Gemini/Groq** brains — note Claude/ChatGPT are listed only as coding assistants, not agent brains). Digest in [docs/02-week1-gate.md](docs/02-week1-gate.md) §3.
2. **Run the spike script**: `backend/spike/nac_spike.py` (fill `.env` from `.env.example` with your RapidAPI key; then again with `SPIKE_MUTATIONS=1`). **The decisive item: the three-legged consent flow for the identity family (NV/KYC/Tenure/Recycling).** Full API inventory: [docs/08-nac-api-catalog.md](docs/08-nac-api-catalog.md). *Note: the RapidAPI key path works even while the NaC portal login is broken — the MCP calls authenticated fine on Jul 6.*
3. **Fix NaC portal login** (password reset / other browser / support@networkascode) — needed for simulator-number management, not for API calls. Confirm the account's simulator numbers (update `DEVICE_PHONE` in `.env` if not `+3670123456`).
4. Form/confirm the team on HackerEarth; download the real Idea Capture Template file.
5. **Jul 12: hold the gate**, append the decision record to doc 02. Standing: **MIZAN 9.0 vs Wakalah 9.0 — a genuine tie**; the consent-flow spike result decides (doc 01, Round 3).
