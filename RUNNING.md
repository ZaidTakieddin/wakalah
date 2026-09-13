# Running Wakalah

Two ways to see it work. Easiest first — no install needed.

## Option A — hosted demo (2 minutes, no install)

- **App:** https://wakalah-balance-demo.vercel.app
- **Home page:** pick a phone number, send `500` to Hessa Al-Mansoori → ALLOW; `1,500` to Omar Cafe → CHALLENGE; `5,000` → DENY.
- **Scenario page (`/scenario`):** press the beats 1 → 7 in order. Routine allows on 1 check, the cloned-agent attempt denies with hijack + continuity codes, the outage beat challenges instead of approving.
- **Backend directly:** https://wakalah.onrender.com/health · interactive API docs at https://wakalah.onrender.com/docs

## Option B — run locally (Python 3.12+, Node 22+)

Backend (from `backend/`):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then set NAC_MODE=replay (no keys needed)
python -m uvicorn app.main:app --port 8000
```

Frontend (from `frontend/wakalah-balance-demo/`, second terminal):

```bash
npm install
printf 'WAKALAH_API_BASE=http://127.0.0.1:8000\nNEXT_PUBLIC_WAKALAH_WS_URL=ws://127.0.0.1:8000/ws\n' > .env.local
npm run dev                   # open http://localhost:3000
```

Notes:

- `NAC_MODE=replay` serves recorded real sandbox responses — the full demo works with zero API keys. For live network calls, set `NAC_MODE=live` and add `RAPIDAPI_KEY` + `GEMINI_API_KEY` to `backend/.env` (see `.env.example`).
- Every signal carries a honesty label (`live` / `cached` / `replay` / `simulated` / `unavailable`), rendered on screen — replayed values are never presented as live.
- Verify the backend: `pytest` in `backend/` (129 offline tests, ~2 s), plus `ruff check .` and `mypy app`.
