# Wakalah — MENA Ignite Hackathon (GSMA)

Trust layer for AI-agent transactions, built on Nokia Network-as-Code CAMARA APIs.
New here (human or AI)? Read [docs/09-master-explanation.md](docs/09-master-explanation.md) first — every term and decision explained from zero.

## Golden rules (non-negotiable)

1. **No secrets in git.** Keys live in `.env` files (git-ignored). If a key ever lands in history, rotate it — deleting the line is not enough.
2. **$0 rule.** Every tool/service pinned to a free tier; nothing may require a credit card (docs/09 §6).
3. **Tooling-guide compliance.** The product's runtime agent brains are Gemini / Groq / Ollama only, on LangGraph + Pydantic AI. Claude/ChatGPT are approved as *coding assistants*, never as runtime brains (docs/02 §3).
4. **Agents propose, policy disposes.** LLM output never mutates state directly; the deterministic policy layer has final authority on every verdict *and* enforces a minimum verification-check floor per risk tier (the agent may escalate above it, never plan below it). See docs/04 §4.
5. **NacClient is the only door to NaC.** No HTTP calls to Network-as-Code outside `backend/app/nac/`.
6. **Deterministic demo.** The scenario engine drives the story; the replay cache is the fallback; no wall-clock-dependent behavior in demo paths.
7. **Honesty ledger.** Every synthetic/simulated input is declared in `SYNTHETIC_DATA.md` and labeled in the UI.
8. **Update the master explanation.** After any significant step: append a D-entry to docs/09 §3 (chronologically — *after* the last entry), a §7 changelog line, and glossary entries for new terms. Use the `/log-decision` skill.
9. **Commit hygiene is originality evidence.** Small commits, real messages, both members committing — the history proves the code was written inside the hackathon window (Jul 1 – Sep 13, 2026).

## Repo map

- `backend/` (Zaid) — FastAPI + agents + NaC + Supabase. Rules: [backend/CLAUDE.md](backend/CLAUDE.md)
- `frontend/` (teammate) — split-screen demo UI over the WebSocket contract (docs/07 §3). Add `frontend/CLAUDE.md` with its own rules when scaffolding.
- `docs/` — strategy, specs, submission drafts. Index: [README.md](README.md)
- Root — assistant/project config only: `CLAUDE.md`, `.mcp.json`, `.claude/` (skills), `.gitignore`

## Key facts the code must respect

- Simulator personas: clean = `+99999991001`, compromised = `+99999991000`, `04xx/05xx` numbers return that HTTP error (docs/02 §5.6).
- Supabase is server-side only (service key in `backend/.env`); the frontend never touches it — it speaks only the FastAPI WebSocket/REST contract.
- Deadlines that shape scope: deck screenshots ~Aug 10 · Phase-1 submit Aug 20 · video Sep 8 · final Sep 11 (docs/06).
