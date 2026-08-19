---
name: log-decision
description: Append a project decision to docs/09-master-explanation.md — decision log entry, changelog line, and glossary entries for any new terms. Use after any significant step, decision, or lesson learned.
---

Append the decision the user describes (or the one just taken in this session) to `docs/09-master-explanation.md`, keeping the file's contract: written for a reader who knows nothing about NaC, telecom, or AI agents.

Steps:

1. Read the end of §3 (Decision Log) to find the highest D-number and the final entry's closing text.
2. Write the new entry as `**D<next> (<date>) — <short title>.**` followed by 3–6 sentences: what was decided, the plain-language *why*, what it replaced or changed, and any consequence worth remembering (including honest trade-offs).
3. **Anchor the insert on the END of the last decision's paragraph** so the log stays chronological — past mistakes in this repo came from anchoring on the *next* section's heading and accidentally prepending. Verify order after editing.
4. Append or extend the matching date line in §7 (Changelog) with a one-clause summary + the D-number.
5. If the decision introduced terms not yet in §2 (Glossary), add them to the right subsection, one plain-English sentence each, no circular definitions.
6. If the decision contradicts an older entry or section (e.g., a tool swap), do NOT rewrite history — the old entry stands; the new entry states what changed and why. Update any *non-log* sections (§5, §6 tables) to the new truth.
7. Match the file's voice: plain English, newcomer-friendly, honest about trade-offs, no unexplained jargon.
