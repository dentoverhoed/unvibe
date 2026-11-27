---
name: kickstart
description: Use when the user types /kickstart (optionally with an action ID like F1, V1, S1, or "status", "workflow", "again"), or explicitly asks to audit, onboard or set up a codebase for AI-assisted coding ("make this project agent-ready", "audit this vibe-coded project", "kickstart this repo"). Works for new and existing (vibe-coded) projects.
---

# /kickstart: project audit and setup for AI-assisted coding

The full procedure is in `runbook.md`, in the same folder as this file. **Read only the sections the route below names.** Refer to sections by their heading, not by line number.

## Choosing the route from the arguments

| Argument | What you do | Read in `runbook.md` |
|---|---|---|
| *(none)* | **Phases 0–2**: detection, read-only audit or intake, report, then ⛔ STOP and ask which action items may be carried out | "Ground rules", "Phase 0", "Phase 1A" (existing) **or** "Phase 1B" (new), "Phase 2", Appendices A, B, C |
| One or more action IDs, e.g. `F1`, `S1 V1` | **Phase 3** for that ID, **one ID per session** (if several: do the first and list the rest) | "Ground rules", the intro of "Phase 3", the block matching the letter (S → "Security-urgent" row in the Phase 2 table; F, V, H, T, R, Re, A, Au), Appendices D, E, F |
| `status` | Summarise `docs/agents/kickstart-status.md`: what is done, which ID is next. Change nothing. | none |
| `workflow` | Explain the daily workflow, applied to this project | "Phase 4" |
| `again` | Run a new audit, then compare its scorecard with the previous `docs/agents/audit-*.md` | as for *(none)*, plus the previous audit |

**Precondition for Phase 3:** `docs/agents/kickstart-status.md` exists, and a `docs/agents/audit-*.md` lists the ID.
- Missing? Say so and suggest running `/kickstart` without arguments first.
- The ID is not in the action list? Show the available IDs.

## Always applies (short version; the full set is in "Ground rules")

- **Phases 1 and 2 are read-only.** You write only under `docs/agents/`.
- **Every ⛔ STOP is a real stop.** Your final answer is the question to the user.
- **Configuration is proposed as a diff** and applied only after approval. This covers hooks, permissions, CI and lint rules.
- **Prove every new check bites:** it passes, fails on a temporary violation, and passes again after the revert.
- **Secrets:** never print values.
- **Every session:** update `docs/agents/kickstart-status.md` with the date and commit hash.
- **Language:** reply and write reports in the user's language.

## Final answer to the user

| After | Final answer |
|---|---|
| Phase 2 | At most 15 lines: scorecard, top 5 action items with IDs, and the choice question. Then: "Next step: `/kickstart <ID>`". |
| Phase 3 | What was done, the evidence that it works, a link to the branch or PR, and the next ID from the status. |
