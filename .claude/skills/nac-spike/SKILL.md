---
name: nac-spike
description: Run the Nokia Network-as-Code sandbox spike and record results — executes the spike script, compares against previous findings, and updates the gate doc. Use when re-verifying NaC API behavior or testing a new API/persona.
---

Run the NaC spike and keep the evidence trail current.

Steps:

1. Preflight: confirm `backend/spike/.env` exists with `RAPIDAPI_KEY` set (never print its value). If Python is installed, prefer `python backend/spike/nac_spike.py`; otherwise run `powershell -ExecutionPolicy Bypass -File backend/spike/nac_spike.ps1` (add `-Mutations` for the QoD + geofencing create/delete pass — both clean up after themselves).
2. Read `backend/spike/spike-results.json` (and `persona-matrix.json` if the persona probe ran).
3. Compare against the recorded findings in `docs/02-week1-gate.md` §5.5–5.6. Only differences matter: new failures, changed response shapes, changed persona behavior, new rate-limit signs (429s).
4. Update the tables in doc 02 if anything changed, dated. If a *core-chain* API regressed (Number Verification family, SIM Swap, geofencing), flag it loudly in the reply — that's demo risk, not trivia.
5. Surprising findings also get a `/log-decision` entry if they change a decision or design.
6. Keep raw JSON files — they seed the replay cache (`backend/app/nac/replay.py` once scaffolded).

Testing a specific API or persona: adjust `DEVICE_PHONE` in `.env` (roster + personas documented in `docs/02` §5.6 and `backend/spike/.env.example`) or add the endpoint to the script's table, mirroring the existing entries in BOTH script variants (.py and .ps1).
