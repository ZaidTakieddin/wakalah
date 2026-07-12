# Backend rules (Python / FastAPI)

Stack: Python 3.12+, FastAPI, Pydantic v2, LangGraph + Pydantic AI (agent layer), supabase-py (storage), pytest. Tool config lives in [pyproject.toml](pyproject.toml).

## Quality gates — run before every push

```
ruff check . ; ruff format --check .   # lint + formatting
mypy app                               # types — public functions fully annotated
pytest                                 # required suites below
```

Before merging a significant PR: run the built-in `/code-review` (medium effort) and fix or consciously dismiss findings.

## Architecture invariants (violating these = the PR is wrong, not the rule)

1. **`app/nac/` (NacClient) is the only module that talks to NaC.** Implementations: REST (primary), replay (fallback). Every call emits a `nac.call` event carrying latency and a `simulated` flag.
2. **`app/agents/` is the only guide-restricted zone** — LangGraph/Pydantic AI with Gemini/Groq/Ollama brains. Agents return *typed proposals*; they never write to the DB or call external services except through the tools they are given.
3. **`app/policy/` is deterministic** — no LLM, no randomness, no wall clock. It has final authority on every verdict. Rules live in versioned YAML next to the code.
4. **All cross-layer communication is typed events** (`app/models/events.py`) — one schema feeding both the WebSocket stream and the audit log. Never emit ad-hoc dicts.
5. **Storage goes through `app/store/` repositories** (supabase-py). No inline queries elsewhere. Schema changes are numbered SQL files in `supabase/migrations/` — append new migrations, never edit past ones.
6. **Errors are typed and preserved.** Raise typed exceptions; map to the CAMARA-style `{status, code, message}` shape at the API boundary. Never swallow NaC errors — the 04xx/05xx personas are demo material, and the Sentinel's graceful-degradation beat depends on seeing them.

## Style

- Type hints on everything public; Pydantic models at every I/O boundary.
- Small modules over clever ones; plain-English docstrings using the glossary terms (docs/09 §2).
- Comments only for constraints the code can't express — never to narrate what a line does.
- Secrets from env only (`backend/.env`, git-ignored; keep `.env.example` current whenever a new variable appears).
- Structured JSON logs; include the `x-correlator` id on NaC calls.

## Tests (pytest, mirroring `app/` layout under `tests/`)

- **Policy gates**: table-driven cases per rule, including boundary values.
- **Scenario determinism**: same scripted input → identical event sequence, twice.
- **Replay parity**: the recorded response set must pass the same assertions as live calls.
- Agents: test the *contract* (typed proposal in/out with a stubbed brain), not the LLM's prose.
