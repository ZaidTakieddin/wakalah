# Wakalah — Demo UI

React 19 + Vite + TypeScript + Tailwind 4.

## 👉 Read this first

**[docs/10-frontend-guide.md](../docs/10-frontend-guide.md)** — the full integration guide: every endpoint, every live event, TypeScript types, and how the data should be presented on screen.

## Run it

```bash
# terminal 1 — backend (from ../backend)
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload

# terminal 2 — here
npm install
npm run dev
```

No API keys needed on this side: the backend holds every credential. The UI only talks to `http://127.0.0.1:8000`.

- Health: <http://127.0.0.1:8000/health>
- Interactive API docs: <http://127.0.0.1:8000/docs>
- Live event stream: `ws://127.0.0.1:8000/ws`

## The three things the UI must show

1. **The agent's plan changing with risk** — 1 check for a routine payment, 7–8 for a risky one. This is what the hackathon scores under "Agentic AI & Multi-API Orchestration."
2. **AI proposing vs policy deciding** — style agent steps and policy steps differently; when `policyOverrodeAgent` is true, show both side by side.
3. **Honesty labels** — every signal carries `source` (`live` / `cached` / `replay` / `simulated` / `unavailable`). Render it always. Never show a cached value as if it were live.

## One constraint that shapes everything

**A decision takes 5–25 seconds.** Subscribe to the WebSocket and render each step as it arrives — never a 20-second spinner. The wait is the show: the audience watches the agent think.
